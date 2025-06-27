/**
 * Azure Speech Services client for text-to-speech synthesis
 * Following Azure best practices with managed identity authentication
 */

import { 
  SpeechConfig, 
  AudioConfig, 
  SpeechSynthesizer, 
  ResultReason,
  SpeechSynthesisResult
} from 'microsoft-cognitiveservices-speech-sdk';
import { DefaultAzureCredential } from '@azure/identity';
import { SecretClient } from '@azure/keyvault-secrets';

export interface ISpeechClient {
  synthesizeSpeech(text: string, voice?: string): Promise<ArrayBuffer>;
  getAvailableVoices(): Promise<string[]>;
}

export class SpeechClient implements ISpeechClient {
  private speechConfig: SpeechConfig;
  private defaultVoice: string;

  constructor() {
    this.defaultVoice = process.env.AZURE_SPEECH_VOICE || 'en-US-AriaNeural';
    this.initializeSpeechConfig();
  }

  private async initializeSpeechConfig(): Promise<void> {
    const speechKey = await this.getSpeechKey();
    const speechRegion = process.env.AZURE_SPEECH_REGION || 'eastus';

    this.speechConfig = SpeechConfig.fromSubscription(speechKey, speechRegion);
    this.speechConfig.speechSynthesisVoiceName = this.defaultVoice;
    
    // Configure audio format for high quality
    this.speechConfig.speechSynthesisOutputFormat = 5; // Audio24Khz48KBitRateMonoMp3
  }

  private async getSpeechKey(): Promise<string> {
    // First try environment variable (for local development)
    const envKey = process.env.AZURE_SPEECH_KEY;
    if (envKey) {
      return envKey;
    }

    // Production: retrieve from Key Vault using managed identity
    try {
      const credential = new DefaultAzureCredential();
      const vaultUrl = process.env.AZURE_KEYVAULT_URL;
      
      if (!vaultUrl) {
        throw new Error('AZURE_KEYVAULT_URL not configured');
      }

      const client = new SecretClient(vaultUrl, credential);
      const secret = await client.getSecret('speech-service-key');
      
      if (!secret.value) {
        throw new Error('Speech service key not found in Key Vault');
      }

      return secret.value;
    } catch (error) {
      throw new Error(`Failed to retrieve speech key: ${error}`);
    }
  }

  async synthesizeSpeech(text: string, voice?: string): Promise<ArrayBuffer> {
    if (!this.speechConfig) {
      await this.initializeSpeechConfig();
    }

    // Update voice if specified
    if (voice && voice !== this.speechConfig.speechSynthesisVoiceName) {
      this.speechConfig.speechSynthesisVoiceName = voice;
    }

    return new Promise((resolve, reject) => {
      const audioConfig = AudioConfig.fromDefaultSpeakerOutput();
      const synthesizer = new SpeechSynthesizer(this.speechConfig, audioConfig);

      // Create SSML with voice and prosody controls for better podcast delivery
      const ssml = this.createSSML(text, voice || this.defaultVoice);

      synthesizer.speakSsmlAsync(
        ssml,
        (result: SpeechSynthesisResult) => {
          synthesizer.close();

          if (result.reason === ResultReason.SynthesizingAudioCompleted) {
            resolve(result.audioData);
          } else {
            reject(new Error(`Speech synthesis failed: ${result.errorDetails}`));
          }
        },
        (error) => {
          synthesizer.close();
          reject(new Error(`Speech synthesis error: ${error}`));
        }
      );
    });
  }

  private createSSML(text: string, voice: string): string {
    // Create SSML with prosody controls for engaging podcast delivery
    return `
      <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">
        <voice name="${voice}">
          <prosody rate="0.9" pitch="+2Hz">
            ${this.escapeXml(text)}
          </prosody>
        </voice>
      </speak>
    `;
  }

  private escapeXml(text: string): string {
    return text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&apos;');
  }

  async getAvailableVoices(): Promise<string[]> {
    // Common Azure neural voices for podcast generation
    return [
      'en-US-AriaNeural',
      'en-US-GuyNeural', 
      'en-US-JennyNeural',
      'en-US-DavisNeural',
      'en-GB-LibbyNeural',
      'en-GB-RyanNeural',
      'en-AU-NatashaNeural',
      'en-CA-ClaraNeural'
    ];
  }
}

// Factory function for dependency injection
export function createSpeechClient(): ISpeechClient {
  return new SpeechClient();
}
