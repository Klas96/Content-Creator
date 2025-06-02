import os
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional
from moviepy.video.io.ImageSequenceClip import ImageSequenceClip
from moviepy.audio.io.AudioFileClip import AudioFileClip
# Not needed for simplified audio: CompositeAudioClip, AudioClip, numpy
from ..config import TEST_MODE
from .base import ContentGenerator

class VideoGenerator(ContentGenerator):
    def __init__(self, config: dict = None):
        super().__init__(config)
        self.output_video_path = None
        self._thread_pool = ThreadPoolExecutor() # For running moviepy in a separate thread

    async def _create_video_logic(
        self,
        image_paths: List[str],
        audio_path: str, # This is now the pre-mixed final audio
        output_path: str,
        video_prompt: Optional[str] = None, # video_prompt is not used in current moviepy logic
        content_type: str = "story", # content_type might influence fps or transitions in future
        fps: int = 1
    ):
        """
        Core logic to create a video from images and a final audio track.
        Runs in a thread pool to avoid blocking asyncio event loop.
        """
        # Verify all input files exist
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Required audio file not found: {audio_path}")
        for img_path in image_paths:
            if not os.path.exists(img_path):
                raise FileNotFoundError(f"Required image file not found: {img_path}")

        clip = None
        final_audio_clip = None
        try:
            # Create video from images
            # TODO: Make fps configurable via self.config or method params
            clip = ImageSequenceClip(image_paths, fps=fps)
            
            # Load the final audio track
            final_audio_clip = AudioFileClip(audio_path)

            # Set the audio of the video
            clip = clip.with_audio(final_audio_clip)

            # Ensure clip duration matches audio duration, or vice-versa.
            # MoviePy usually handles this by making video match audio or vice-versa.
            # If specific behavior is needed (e.g. extend last frame, loop video), implement here.
            if clip.duration > final_audio_clip.duration:
                clip = clip.subclip(0, final_audio_clip.duration)
            elif final_audio_clip.duration > clip.duration:
                # This might extend the last frame of the clip to match audio duration.
                # Or, if audio is much longer, it might be an issue.
                # For now, default moviepy behavior is accepted.
                pass


            # Create output directory if it doesn't exist
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # Write the result to a file
            # TODO: Make codec, audio_codec configurable
            clip.write_videofile(output_path, codec='libx264', audio_codec='aac')

            self.output_video_path = output_path
            self.status = "completed"
            return output_path
        
        except Exception as e:
            self.status = f"failed: {e}"
            raise
        finally:
            # Clean up resources
            if final_audio_clip:
                final_audio_clip.close()
            if clip:
                clip.close()

    async def generate(
        self,
        image_paths: List[str],
        audio_path: str, # This is now the pre-mixed final audio
        output_video_path: str,
        video_prompt: Optional[str] = None,
        content_type: str = "story", # Example: could be used for fps selection
        **kwargs
    ):
        self.status = "processing"
        self.output_video_path = output_video_path # Store intended path early

        if TEST_MODE:
            # Create a dummy video file for testing
            os.makedirs(os.path.dirname(output_video_path), exist_ok=True)
            with open(output_video_path, "w") as f:
                f.write("This is a dummy video file.")
            self.status = "completed"
            self.output = output_video_path # self.output is from base class, maybe use self.output_video_path
            return output_video_path

        try:
            # Run the synchronous moviepy logic in a thread pool
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                self._thread_pool,
                self._create_video_logic, # Target synchronous blocking function
                image_paths,
                audio_path,
                output_video_path,
                video_prompt,
                content_type,
                kwargs.get("fps", 1) # Allow fps override via kwargs
            )
            # _create_video_logic sets self.status and self.output_video_path
        except Exception as e:
            self.status = f"failed: {e}" # Capture errors from executor
            # Re-raise if generate is expected to throw
            raise
        return self.output_video_path


    def get_status(self) -> str:
        if self.status == "completed":
            if self.output_video_path and os.path.exists(self.output_video_path):
                return "completed"
            else:
                # This indicates completion was reported but file is missing.
                self.status = "failed: output video file missing"
        return self.status

    def get_output(self):
        return self.output_video_path

    def __del__(self):
        # Clean up the thread pool when the generator is deleted
        self._thread_pool.shutdown(wait=False)