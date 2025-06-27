/**
 * Activity functions for podcast generation pipeline
 * Each function is idempotent and handles specific tasks
 */

import { ActivityHandler } from 'durable-functions';
import { BlobServiceClient } from '@azure/storage-blob';
import { CosmosClient } from '@azure/cosmos';
import { chromium } from 'playwright';
import * as cheerio from 'cheerio';
import { v4 as uuidv4 } from 'uuid';
import { Episode, EpisodeStatus, LearningModule } from '../models/Episode';
import { createSpeechClient } from '../clients/SpeechClient';

/**
 * Fetch learning path and extract module URLs using web scraping
 */
export const fetchLearningPath: ActivityHandler = async function (context, learningPathUrl: string) {
  context.log.info(`Fetching learning path: ${learningPathUrl}`);

  try {
    const browser = await chromium.launch({ headless: true });
    const page = await browser.newPage();
    
    // Navigate to the learning path
    await page.goto(learningPathUrl, { waitUntil: 'networkidle' });
    
    // Extract module information from the page
    const modules = await page.evaluate(() => {
      const moduleElements = document.querySelectorAll('[data-module-id], .module-item, .learning-path-module');
      const modules: LearningModule[] = [];
      
      moduleElements.forEach((element, index) => {
        const titleElement = element.querySelector('h3, h4, .module-title, [data-module-title]');
        const linkElement = element.querySelector('a[href*="/training/modules/"]');
        const descElement = element.querySelector('.module-description, .description, p');
        
        if (titleElement && linkElement) {
          const title = titleElement.textContent?.trim() || `Module ${index + 1}`;
          const href = (linkElement as HTMLAnchorElement).href;
          const description = descElement?.textContent?.trim() || '';
          
          modules.push({
            id: `module-${index + 1}`,
            title,
            description,
            url: href,
            order: index + 1,
            hasEpisode: false
          });
        }
      });
      
      return modules;
    });

    await browser.close();
    
    context.log.info(`Found ${modules.length} modules in learning path`);
    return modules;

  } catch (error) {
    context.log.error(`Failed to fetch learning path: ${error}`);
    throw new Error(`Learning path fetch failed: ${error}`);
  }
};

/**
 * Scrape content from a specific module URL
 */
export const scrapeModuleContent: ActivityHandler = async function (context, moduleUrl: string) {
  context.log.info(`Scraping module content: ${moduleUrl}`);

  try {
    const browser = await chromium.launch({ headless: true });
    const page = await browser.newPage();
    
    await page.goto(moduleUrl, { waitUntil: 'networkidle' });
    
    // Extract main content
    const content = await page.evaluate(() => {
      // Remove navigation, ads, and other non-content elements
      const elementsToRemove = [
        'nav', 'header', 'footer', '.navigation', '.breadcrumb', 
        '.table-of-contents', '.feedback', '.next-steps'
      ];
      
      elementsToRemove.forEach(selector => {
        document.querySelectorAll(selector).forEach(el => el.remove());
      });
      
      // Extract main content area
      const contentSelectors = [
        '.content', 'main', '.main-content', '.module-content', 
        '[role="main"]', '.docs-content'
      ];
      
      let mainContent = '';
      for (const selector of contentSelectors) {
        const element = document.querySelector(selector);
        if (element) {
          mainContent = element.textContent || '';
          break;
        }
      }
      
      // Fallback to body if no content area found
      if (!mainContent) {
        mainContent = document.body.textContent || '';
      }
      
      // Clean up the text
      return mainContent
        .replace(/\s+/g, ' ')
        .replace(/\n\s*\n/g, '\n\n')
        .trim();
    });

    await browser.close();
    
    if (!content || content.length < 100) {
      throw new Error('Insufficient content extracted from module');
    }
    
    context.log.info(`Extracted ${content.length} characters of content`);
    return { text: content, url: moduleUrl };

  } catch (error) {
    context.log.error(`Failed to scrape module content: ${error}`);
    throw new Error(`Module scraping failed: ${error}`);
  }
};

/**
 * Generate audio from script using Azure Speech Services
 */
export const generateAudio: ActivityHandler = async function (context, input: { script: string; voice: string; title: string }) {
  context.log.info(`Generating audio for: ${input.title}`);

  try {
    const speechClient = createSpeechClient();
    
    // Generate audio
    const audioBuffer = await speechClient.synthesizeSpeech(input.script, input.voice);
    
    // Upload to Azure Blob Storage
    const blobServiceClient = new BlobServiceClient(process.env.AZURE_STORAGE_CONNECTION_STRING!);
    const containerClient = blobServiceClient.getContainerClient('audio');
    
    // Ensure container exists
    await containerClient.createIfNotExists({ access: 'blob' });
    
    const blobName = `${uuidv4()}-${input.title.replace(/[^a-zA-Z0-9]/g, '-')}.mp3`;
    const blockBlobClient = containerClient.getBlockBlobClient(blobName);
    
    await blockBlobClient.uploadData(audioBuffer, {
      blobHTTPHeaders: {
        blobContentType: 'audio/mpeg'
      }
    });
    
    const audioUrl = blockBlobClient.url;
    
    // Estimate duration (rough calculation: ~150 words per minute)
    const wordCount = input.script.split(/\s+/).length;
    const estimatedDuration = Math.round((wordCount / 150) * 60); // seconds
    
    context.log.info(`Audio generated successfully: ${audioUrl}`);
    
    return {
      blobUrl: audioUrl,
      duration: estimatedDuration,
      wordCount
    };

  } catch (error) {
    context.log.error(`Audio generation failed: ${error}`);
    throw new Error(`Audio generation failed: ${error}`);
  }
};

/**
 * Store episode metadata in Cosmos DB
 */
export const storeEpisode: ActivityHandler = async function (context, episodeData: any) {
  context.log.info(`Storing episode: ${episodeData.title}`);

  try {
    const cosmosClient = new CosmosClient(process.env.COSMOS_DB_CONNECTION!);
    const database = cosmosClient.database('edutainment-forge');
    const container = database.container('episode');
    
    const episode: Episode = {
      id: uuidv4(),
      learningPathId: episodeData.learningPathId || 'default',
      moduleId: episodeData.moduleId,
      title: episodeData.title,
      description: episodeData.description || '',
      script: episodeData.script,
      audioUrl: episodeData.audioUrl,
      duration: episodeData.duration,
      wordCount: episodeData.wordCount,
      status: episodeData.status || EpisodeStatus.Completed,
      sourceUrl: episodeData.sourceUrl,
      createdAt: new Date(),
      updatedAt: new Date(),
      tags: ['ai-900', 'azure', 'learning'] // TODO: Extract from content
    };

    const { resource } = await container.items.create(episode);
    
    context.log.info(`Episode stored successfully: ${resource?.id}`);
    return resource;

  } catch (error) {
    context.log.error(`Failed to store episode: ${error}`);
    throw new Error(`Episode storage failed: ${error}`);
  }
};
