/**
 * Episode model for podcast metadata storage
 */

export interface Episode {
  id: string;
  learningPathId: string;
  moduleId: string;
  title: string;
  description: string;
  script: string;
  audioUrl: string;
  duration: number;
  wordCount: number;
  status: EpisodeStatus;
  sourceUrl: string;
  createdAt: Date;
  updatedAt: Date;
  tags: string[];
}

export enum EpisodeStatus {
  Created = 'created',
  Processing = 'processing',
  Completed = 'completed',
  Failed = 'failed'
}

export interface LearningPath {
  id: string;
  title: string;
  description: string;
  url: string;
  modules: LearningModule[];
  episodeCount: number;
  totalDuration: number;
  createdAt: Date;
  updatedAt: Date;
}

export interface LearningModule {
  id: string;
  title: string;
  description: string;
  url: string;
  order: number;
  duration?: number;
  hasEpisode: boolean;
}

export interface PodcastGenerationRequest {
  learningPathUrl: string;
  moduleUrls?: string[];
  voice?: string;
  includeIntro?: boolean;
  includeOutro?: boolean;
}

export interface PodcastGenerationResult {
  episodeId: string;
  status: EpisodeStatus;
  audioUrl?: string;
  error?: string;
}
