/**
 * Generate Podcast Orchestrator
 * Azure Durable Function that orchestrates the podcast generation workflow
 * Following the blueprint pattern for error handling and retry logic
 */

import { OrchestrationContext, OrchestrationHandler } from 'durable-functions';
import { Episode, EpisodeStatus, PodcastGenerationRequest, LearningModule } from '../models/Episode';

export const generatePodcastOrchestrator: OrchestrationHandler = function* (context: OrchestrationContext) {
  const request: PodcastGenerationRequest = context.df.getInput();
  
  try {
    context.log.info(`Starting podcast generation for: ${request.learningPathUrl}`);

    // Step 1: Fetch learning path and extract module URLs
    const modules: LearningModule[] = yield context.df.callActivity('fetchLearningPath', request.learningPathUrl);
    
    if (!modules || modules.length === 0) {
      throw new Error('No modules found in learning path');
    }

    // Step 2: Process modules in parallel (with concurrency limit)
    const episodePromises = modules.slice(0, 5).map((module, index) => 
      context.df.callSubOrchestrator('processModuleOrchestrator', {
        module,
        request,
        order: index + 1
      })
    );

    const episodes: Episode[] = yield context.df.Task.all(episodePromises);

    // Step 3: Create playlist/RSS feed metadata
    const playlistResult = yield context.df.callActivity('createPlaylist', {
      learningPathUrl: request.learningPathUrl,
      episodes
    });

    context.log.info(`Podcast generation completed. Generated ${episodes.length} episodes`);

    return {
      success: true,
      episodeCount: episodes.length,
      playlistUrl: playlistResult.rssUrl,
      episodes: episodes.map(ep => ({
        id: ep.id,
        title: ep.title,
        audioUrl: ep.audioUrl,
        duration: ep.duration
      }))
    };

  } catch (error) {
    context.log.error(`Podcast generation failed: ${error}`);
    
    // Store failure information
    yield context.df.callActivity('logFailure', {
      request,
      error: error instanceof Error ? error.message : String(error),
      timestamp: new Date()
    });

    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error occurred'
    };
  }
};

/**
 * Sub-orchestrator for processing individual modules
 * Handles the content-to-audio pipeline for a single module
 */
export const processModuleOrchestrator: OrchestrationHandler = function* (context: OrchestrationContext) {
  const { module, request, order } = context.df.getInput();
  
  try {
    context.log.info(`Processing module: ${module.title}`);

    // Step 1: Scrape module content
    const rawContent = yield context.df.callActivity('scrapeModuleContent', module.url);

    // Step 2: Generate engaging script using Azure OpenAI
    const script = yield context.df.callActivity('summarizeAndScript', {
      content: rawContent,
      title: module.title,
      order
    });

    // Step 3: Generate audio using Azure Speech Services
    const audioResult = yield context.df.callActivity('generateAudio', {
      script: script.text,
      voice: request.voice || 'en-US-AriaNeural',
      title: module.title
    });

    // Step 4: Store episode metadata and files
    const episode: Episode = yield context.df.callActivity('storeEpisode', {
      moduleId: module.id,
      title: module.title,
      description: script.description,
      script: script.text,
      audioUrl: audioResult.blobUrl,
      duration: audioResult.duration,
      wordCount: script.wordCount,
      sourceUrl: module.url,
      order
    });

    context.log.info(`Module processing completed: ${episode.id}`);
    return episode;

  } catch (error) {
    context.log.error(`Module processing failed for ${module.title}: ${error}`);
    
    // Create failed episode record
    const failedEpisode: Episode = yield context.df.callActivity('storeEpisode', {
      moduleId: module.id,
      title: module.title,
      status: EpisodeStatus.Failed,
      script: '',
      audioUrl: '',
      duration: 0,
      wordCount: 0,
      sourceUrl: module.url,
      error: error instanceof Error ? error.message : String(error)
    });

    return failedEpisode;
  }
};
