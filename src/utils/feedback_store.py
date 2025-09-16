"""
Feedback storage utility for podcast ratings.

Stores thumbs up/down feedback for podcasts and provides analytics for AI enhancement.
Uses JSON file storage for simplicity in hackathon environment.
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import threading
from utils.logger import get_logger

logger = get_logger(__name__)


class FeedbackStore:
    """Manages podcast feedback storage and retrieval."""
    
    def __init__(self, storage_path: str = "data/feedback.json"):
        """Initialize the feedback store with a JSON file."""
        self.storage_path = Path(storage_path)
        self.lock = threading.Lock()
        self._ensure_storage_exists()
    
    def _ensure_storage_exists(self):
        """Ensure the storage directory and file exist."""
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.storage_path.exists():
            with open(self.storage_path, 'w') as f:
                json.dump({}, f)
    
    def _load_feedback_data(self) -> Dict:
        """Load feedback data from storage."""
        try:
            with open(self.storage_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.warning(f"Could not load feedback data: {e}, starting with empty store")
            return {}
    
    def _save_feedback_data(self, data: Dict):
        """Save feedback data to storage."""
        try:
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save feedback data: {e}")
            raise
    
    def add_feedback(self, podcast_name: str, feedback_type: str, user_id: Optional[str] = None) -> bool:
        """
        Add feedback for a podcast.
        
        Args:
            podcast_name: Name of the podcast file
            feedback_type: 'thumbs_up' or 'thumbs_down'
            user_id: Optional user identifier
            
        Returns:
            True if feedback was successfully added
        """
        if feedback_type not in ['thumbs_up', 'thumbs_down']:
            raise ValueError("feedback_type must be 'thumbs_up' or 'thumbs_down'")
        
        with self.lock:
            try:
                data = self._load_feedback_data()
                
                if podcast_name not in data:
                    data[podcast_name] = {
                        'thumbs_up': [],
                        'thumbs_down': [],
                        'created_at': datetime.now().isoformat(),
                        'metadata': {}
                    }
                
                feedback_entry = {
                    'timestamp': datetime.now().isoformat(),
                    'user_id': user_id or 'anonymous'
                }
                
                # Remove any previous feedback from this user
                if user_id:
                    data[podcast_name]['thumbs_up'] = [
                        f for f in data[podcast_name]['thumbs_up'] 
                        if f.get('user_id') != user_id
                    ]
                    data[podcast_name]['thumbs_down'] = [
                        f for f in data[podcast_name]['thumbs_down'] 
                        if f.get('user_id') != user_id
                    ]
                
                # Add new feedback
                data[podcast_name][feedback_type].append(feedback_entry)
                
                self._save_feedback_data(data)
                logger.info(f"Added {feedback_type} feedback for {podcast_name}")
                return True
                
            except Exception as e:
                logger.error(f"Failed to add feedback: {e}")
                return False
    
    def get_podcast_feedback(self, podcast_name: str) -> Dict:
        """
        Get feedback summary for a specific podcast.
        
        Args:
            podcast_name: Name of the podcast file
            
        Returns:
            Dictionary with thumbs_up_count, thumbs_down_count, and feedback_score
        """
        with self.lock:
            data = self._load_feedback_data()
            
            if podcast_name not in data:
                return {
                    'thumbs_up_count': 0,
                    'thumbs_down_count': 0,
                    'feedback_score': 0.0,
                    'total_feedback': 0
                }
            
            feedback_data = data[podcast_name]
            thumbs_up = len(feedback_data.get('thumbs_up', []))
            thumbs_down = len(feedback_data.get('thumbs_down', []))
            total = thumbs_up + thumbs_down
            
            # Calculate feedback score (0.0 to 1.0, where 1.0 is all positive)
            if total == 0:
                feedback_score = 0.0
            else:
                feedback_score = thumbs_up / total
            
            return {
                'thumbs_up_count': thumbs_up,
                'thumbs_down_count': thumbs_down,
                'feedback_score': feedback_score,
                'total_feedback': total
            }
    
    def get_user_feedback(self, podcast_name: str, user_id: str) -> Optional[str]:
        """
        Get a specific user's feedback for a podcast.
        
        Args:
            podcast_name: Name of the podcast file
            user_id: User identifier
            
        Returns:
            'thumbs_up', 'thumbs_down', or None if no feedback
        """
        with self.lock:
            data = self._load_feedback_data()
            
            if podcast_name not in data:
                return None
            
            feedback_data = data[podcast_name]
            
            # Check thumbs up
            for feedback in feedback_data.get('thumbs_up', []):
                if feedback.get('user_id') == user_id:
                    return 'thumbs_up'
            
            # Check thumbs down
            for feedback in feedback_data.get('thumbs_down', []):
                if feedback.get('user_id') == user_id:
                    return 'thumbs_down'
            
            return None
    
    def get_all_feedback_summary(self) -> Dict:
        """
        Get summary of all feedback across all podcasts.
        
        Returns:
            Dictionary with overall statistics and top/bottom rated podcasts
        """
        with self.lock:
            data = self._load_feedback_data()
            
            if not data:
                return {
                    'total_podcasts': 0,
                    'total_feedback': 0,
                    'average_score': 0.0,
                    'top_rated': [],
                    'bottom_rated': []
                }
            
            podcast_scores = []
            total_feedback = 0
            
            for podcast_name, feedback_data in data.items():
                thumbs_up = len(feedback_data.get('thumbs_up', []))
                thumbs_down = len(feedback_data.get('thumbs_down', []))
                total = thumbs_up + thumbs_down
                
                if total > 0:
                    score = thumbs_up / total
                    podcast_scores.append({
                        'podcast_name': podcast_name,
                        'score': score,
                        'total_feedback': total,
                        'thumbs_up': thumbs_up,
                        'thumbs_down': thumbs_down
                    })
                    total_feedback += total
            
            # Sort by score for top/bottom lists
            podcast_scores.sort(key=lambda x: x['score'], reverse=True)
            
            average_score = 0.0
            if podcast_scores:
                average_score = sum(p['score'] for p in podcast_scores) / len(podcast_scores)
            
            return {
                'total_podcasts': len(data),
                'total_feedback': total_feedback,
                'average_score': average_score,
                'top_rated': podcast_scores[:5],  # Top 5
                'bottom_rated': podcast_scores[-5:] if len(podcast_scores) > 5 else []  # Bottom 5
            }
    
    def get_feedback_insights_for_ai(self) -> Dict:
        """
        Get feedback insights formatted for AI enhancement prompts.
        
        Returns:
            Dictionary with insights about what users like/dislike
        """
        with self.lock:
            data = self._load_feedback_data()
            summary = self.get_all_feedback_summary()
            
            insights = {
                'overall_satisfaction': summary['average_score'],
                'feedback_volume': summary['total_feedback'],
                'top_rated_patterns': [],
                'improvement_areas': [],
                'recommendations': []
            }
            
            # Analyze patterns in highly rated content
            if summary['top_rated']:
                insights['top_rated_patterns'] = [
                    f"Podcast '{p['podcast_name']}' has {p['score']:.0%} positive feedback"
                    for p in summary['top_rated'][:3]
                ]
            
            # Identify improvement areas from low-rated content
            if summary['bottom_rated']:
                insights['improvement_areas'] = [
                    f"Podcast '{p['podcast_name']}' needs improvement ({p['score']:.0%} positive)"
                    for p in summary['bottom_rated'][:3]
                ]
            
            # Generate AI recommendations
            if summary['average_score'] < 0.6:
                insights['recommendations'].append(
                    "Focus on clearer explanations and more engaging dialogue"
                )
            
            if summary['average_score'] > 0.8:
                insights['recommendations'].append(
                    "Current style is working well, maintain conversational tone and technical depth"
                )
            
            if summary['total_feedback'] < 5:
                insights['recommendations'].append(
                    "Limited feedback available, continue with balanced conversational approach"
                )
            
            return insights


# Global instance
_feedback_store = None
_store_lock = threading.Lock()


def get_feedback_store() -> FeedbackStore:
    """Get the global feedback store instance."""
    global _feedback_store
    if _feedback_store is None:
        with _store_lock:
            if _feedback_store is None:
                _feedback_store = FeedbackStore()
    return _feedback_store