import asyncio
from ingestion.ms_learn_ingestor import MSLearnIngestor
from audio.speechGeneration import generate_speech
from audio.ssmlFormatter import format_ssml
from utils.logger import logger

async def process_module(module_id: str, voice: str):
    ingestor = MSLearnIngestor()
    content = ingestor.ingest(module_id)
    ssml_text = format_ssml(content["text"])
    audio = generate_speech(ssml_text, voice)
    # Save or further process audio
    logger.info(f"Processed module {module_id}")

async def process_modules_concurrently(module_ids: list, voice: str):
    tasks = [process_module(mid, voice) for mid in module_ids]
    await asyncio.gather(*tasks)

# Entry point
def run_pipeline(module_ids: list, voice: str):
    asyncio.run(process_modules_concurrently(module_ids, voice))
