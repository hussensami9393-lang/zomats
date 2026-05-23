"""
Image Service - AI Image Generation, Editing, Background Removal
Supports: Pollinations (free), Stability AI, Replicate, OpenAI DALL-E
"""
import httpx
import base64
import io
import os
from typing import Optional, Tuple
from loguru import logger
from config.settings import config
from PIL import Image


class ImageService:
    """
    Comprehensive image AI service:
    - Text-to-image generation
    - Background removal
    - Image enhancement
    - Virtual try-on (clothes change)
    - Image editing with AI
    """
    
    def __init__(self):
        self.http_client = httpx.AsyncClient(timeout=120.0)
    
    # ============================
    # Image Generation
    # ============================
    
    async def generate_image_pollinations(self, prompt: str, width: int = 1024, height: int = 1024) -> Optional[bytes]:
        """
        Generate image using Pollinations AI (FREE, no API key needed)
        """
        try:
            import urllib.parse
            # Enhance prompt for better results
            enhanced_prompt = f"{prompt}, highly detailed, professional quality, 8k, trending on artstation"
            encoded_prompt = urllib.parse.quote(enhanced_prompt)
            
            url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&model=flux&nologo=true&enhance=true"
            
            logger.info(f"🎨 Generating image with Pollinations: {prompt[:50]}...")
            
            response = await self.http_client.get(url, follow_redirects=True)
            
            if response.status_code == 200:
                logger.success("✅ Image generated successfully with Pollinations")
                return response.content
            else:
                logger.error(f"Pollinations error: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Pollinations generation error: {e}")
            return None
    
    async def generate_image_stability(self, prompt: str, negative_prompt: str = "", 
                                        style: str = "enhance") -> Optional[bytes]:
        """
        Generate image using Stability AI API
        """
        if not config.STABILITY_API_KEY:
            return await self.generate_image_pollinations(prompt)
        
        try:
            url = "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image"
            
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Authorization": f"Bearer {config.STABILITY_API_KEY}",
            }
            
            payload = {
                "text_prompts": [
                    {"text": prompt, "weight": 1},
                    {"text": negative_prompt or "blurry, low quality, distorted", "weight": -1}
                ],
                "cfg_scale": 7,
                "height": 1024,
                "width": 1024,
                "steps": 30,
                "samples": 1,
                "style_preset": style,
            }
            
            response = await self.http_client.post(url, headers=headers, json=payload)
            
            if response.status_code == 200:
                data = response.json()
                image_b64 = data["artifacts"][0]["base64"]
                return base64.b64decode(image_b64)
            else:
                logger.error(f"Stability AI error: {response.status_code} - {response.text}")
                return await self.generate_image_pollinations(prompt)
                
        except Exception as e:
            logger.error(f"Stability AI error: {e}")
            return await self.generate_image_pollinations(prompt)
    
    async def generate_image_dalle(self, prompt: str, size: str = "1024x1024",
                                    quality: str = "standard") -> Optional[bytes]:
        """
        Generate image using OpenAI DALL-E 3
        """
        if not config.OPENAI_API_KEY:
            return await self.generate_image_pollinations(prompt)
        
        try:
            import openai
            client = openai.AsyncOpenAI(api_key=config.OPENAI_API_KEY)
            
            response = await client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                n=1,
                size=size,
                quality=quality,
                response_format="url"
            )
            
            image_url = response.data[0].url
            
            # Download the image
            img_response = await self.http_client.get(image_url)
            if img_response.status_code == 200:
                return img_response.content
            
        except Exception as e:
            logger.error(f"DALL-E error: {e}")
            return await self.generate_image_pollinations(prompt)
        
        return await self.generate_image_pollinations(prompt)
    
    async def generate_image(self, prompt: str, model: str = "auto") -> Tuple[Optional[bytes], str]:
        """
        Smart image generation - automatically picks best available model
        Returns (image_bytes, model_used)
        """
        if model == "auto":
            if config.OPENAI_API_KEY:
                model = "dalle"
            elif config.STABILITY_API_KEY:
                model = "stability"
            else:
                model = "pollinations"
        
        if model == "dalle":
            result = await self.generate_image_dalle(prompt)
            return result, "DALL-E 3"
        elif model == "stability":
            result = await self.generate_image_stability(prompt)
            return result, "Stability AI"
        else:
            result = await self.generate_image_pollinations(prompt)
            return result, "Pollinations AI (Free)"
    
    # ============================
    # Background Removal
    # ============================
    
    async def remove_background(self, image_bytes: bytes) -> Optional[bytes]:
        """
        Remove background from an image using remove.bg API or AI
        """
        try:
            # Try using Replicate's background removal model
            if config.REPLICATE_API_TOKEN:
                return await self._remove_bg_replicate(image_bytes)
            
            # Fallback: use rembg library (local processing)
            return await self._remove_bg_local(image_bytes)
            
        except Exception as e:
            logger.error(f"Background removal error: {e}")
            return None
    
    async def _remove_bg_replicate(self, image_bytes: bytes) -> Optional[bytes]:
        """Remove background using Replicate API"""
        try:
            import replicate
            import base64
            
            # Convert to base64 data URL
            b64 = base64.b64encode(image_bytes).decode()
            data_url = f"data:image/png;base64,{b64}"
            
            output = await asyncio.to_thread(
                replicate.run,
                "cjwbw/rembg:fb8af171cfa1616ddcf1242c093f9c46bcada5ad4cf6f2fbe8b81b330ec05c17",
                input={"image": data_url}
            )
            
            if output:
                async with httpx.AsyncClient() as client:
                    response = await client.get(str(output))
                    return response.content
                    
        except Exception as e:
            logger.error(f"Replicate background removal error: {e}")
        
        return await self._remove_bg_local(image_bytes)
    
    async def _remove_bg_local(self, image_bytes: bytes) -> Optional[bytes]:
        """Remove background using rembg (local)"""
        try:
            from rembg import remove
            result = remove(image_bytes)
            return result
        except ImportError:
            logger.warning("rembg not installed, using simple approach")
            return image_bytes
        except Exception as e:
            logger.error(f"Local bg removal error: {e}")
            return image_bytes
    
    # ============================
    # Image Enhancement
    # ============================
    
    async def enhance_image(self, image_bytes: bytes, enhancement_type: str = "general") -> Optional[bytes]:
        """
        Enhance image quality using AI upscaling
        """
        try:
            if config.REPLICATE_API_TOKEN:
                return await self._enhance_replicate(image_bytes, enhancement_type)
            
            # Local enhancement with PIL
            return await self._enhance_local(image_bytes)
            
        except Exception as e:
            logger.error(f"Image enhancement error: {e}")
            return image_bytes
    
    async def _enhance_replicate(self, image_bytes: bytes, enhancement_type: str) -> Optional[bytes]:
        """Enhance image using Replicate (ESRGAN, Real-ESRGAN)"""
        try:
            import replicate
            import base64
            import asyncio
            
            b64 = base64.b64encode(image_bytes).decode()
            data_url = f"data:image/jpeg;base64,{b64}"
            
            # Real-ESRGAN for 4x upscaling
            output = await asyncio.to_thread(
                replicate.run,
                "nightmareai/real-esrgan:42fed1c4974146d4d2414e2be2c5277c7fcf05fcc3a73abf41610695738c1d7b",
                input={
                    "image": data_url,
                    "scale": 2,
                    "face_enhance": enhancement_type == "portrait"
                }
            )
            
            if output:
                async with httpx.AsyncClient() as client:
                    response = await client.get(str(output))
                    return response.content
                    
        except Exception as e:
            logger.error(f"Replicate enhancement error: {e}")
        
        return await self._enhance_local(image_bytes)
    
    async def _enhance_local(self, image_bytes: bytes) -> bytes:
        """Basic local image enhancement using PIL"""
        try:
            from PIL import Image, ImageEnhance, ImageFilter
            import io
            
            img = Image.open(io.BytesIO(image_bytes))
            
            # Enhance sharpness
            enhancer = ImageEnhance.Sharpness(img)
            img = enhancer.enhance(1.5)
            
            # Enhance contrast
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(1.2)
            
            # Enhance brightness slightly
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(1.05)
            
            # Save to bytes
            output = io.BytesIO()
            img.save(output, format="JPEG", quality=95)
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"Local enhancement error: {e}")
            return image_bytes
    
    # ============================
    # Virtual Try-On (Clothes Change)
    # ============================
    
    async def virtual_try_on(self, person_image: bytes, garment_image: bytes) -> Optional[bytes]:
        """
        Virtual clothing try-on using AI
        Puts garment onto the person image
        """
        if not config.REPLICATE_API_TOKEN:
            return None, "يحتاج هذا الخيار إلى مفتاح Replicate API"
        
        try:
            import replicate
            import base64
            import asyncio
            
            person_b64 = base64.b64encode(person_image).decode()
            garment_b64 = base64.b64encode(garment_image).decode()
            
            person_url = f"data:image/jpeg;base64,{person_b64}"
            garment_url = f"data:image/jpeg;base64,{garment_b64}"
            
            logger.info("👗 Starting virtual try-on...")
            
            output = await asyncio.to_thread(
                replicate.run,
                "cuuupid/idm-vton:c871bb9b046607b680449ecbae55fd8c6d945e0a1948644bf2361b3d021d3ff4",
                input={
                    "human_img": person_url,
                    "garm_img": garment_url,
                    "garment_des": "clothing item",
                    "is_checked": True,
                    "is_checked_crop": False,
                    "denoise_steps": 30,
                    "seed": 42,
                }
            )
            
            if output:
                async with httpx.AsyncClient() as client:
                    response = await client.get(str(output))
                    return response.content, None
                    
        except Exception as e:
            logger.error(f"Virtual try-on error: {e}")
            return None, str(e)
        
        return None, "فشل في تغيير الملابس"
    
    # ============================
    # Image Analysis
    # ============================
    
    async def analyze_image(self, image_bytes: bytes, question: str = None, language: str = "ar") -> str:
        """
        Analyze image content using GPT-4 Vision
        """
        if not config.OPENAI_API_KEY:
            return "⚠️ يحتاج تحليل الصور إلى OpenAI API key"
        
        try:
            import openai
            import base64
            
            client = openai.AsyncOpenAI(api_key=config.OPENAI_API_KEY)
            
            b64 = base64.b64encode(image_bytes).decode()
            data_url = f"data:image/jpeg;base64,{b64}"
            
            prompt = question or (
                "صف هذه الصورة بالتفصيل: ما فيها، الألوان، الأشياء، الأشخاص، النص إن وجد، والجو العام" 
                if language == "ar" else
                "Describe this image in detail: what's in it, colors, objects, people, text if any, and overall mood"
            )
            
            response = await client.chat.completions.create(
                model=config.OPENAI_VISION_MODEL,
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": data_url}}
                    ]
                }],
                max_tokens=1000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Image analysis error: {e}")
            return "❌ فشل في تحليل الصورة"
    
    async def get_image_info(self, image_bytes: bytes) -> dict:
        """Get basic image information"""
        try:
            img = Image.open(io.BytesIO(image_bytes))
            return {
                "format": img.format,
                "mode": img.mode,
                "size": img.size,
                "width": img.width,
                "height": img.height,
            }
        except Exception:
            return {}
    
    async def close(self):
        await self.http_client.aclose()


# Global image service instance
image_service = ImageService()
