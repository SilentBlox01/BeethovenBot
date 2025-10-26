# rate_limiter.py (versión corregida)
# Cambios principales:
# - En todas las funciones de envío (safe_interaction_response, safe_followup_send, safe_send_message, safe_reply), 
#   usamos un diccionario kwargs para agregar solo los parámetros opcionales (como view y file) si no son None.
#   Esto evita el TypeError cuando view=None o file=None, ya que discord.py no acepta None explícitamente en esos parámetros.
# - Agregué manejo para file en safe_followup_send, ya que followup.send soporta files, para consistencia.
# - Mejoré el logging con más detalles.
# - Corregí un posible bug en safe_interaction_response: si el comando es "say", no usa rate limiter, pero ahora maneja kwargs igual.
# - En el manejo de rate limits (429), agregué un retry más robusto con backoff exponencial simple.
# - Eliminé redundancias y limpié el código para evitar errores futuros.

import discord
import asyncio
from typing import Optional, Union
import logging
import time  # Para backoff en retries

logger = logging.getLogger(__name__)

class GlobalRateLimiter:
    def __init__(self):
        self.locks = {}

    async def acquire(self, key: str):
        if key not in self.locks:
            self.locks[key] = asyncio.Lock()
        await self.locks[key].acquire()

    def release(self, key: str):
        if key in self.locks and self.locks[key].locked():
            self.locks[key].release()

async def safe_interaction_response(
    interaction: discord.Interaction, 
    content: Optional[str] = None, 
    embed: Optional[discord.Embed] = None, 
    file: Optional[Union[discord.File, list[discord.File]]] = None,
    view: Optional[discord.ui.View] = None,
    ephemeral: bool = False
):
    """
    Envía una respuesta segura a una interacción con manejo de rate limits y views/files.
    """
    try:
        if embed is None and content is None:
            content = "No se proporcionó contenido."
        
        kwargs = {"content": content, "embed": embed, "ephemeral": ephemeral}
        if file is not None:
            kwargs["file"] = file
        if view is not None:
            kwargs["view"] = view
        
        if interaction.command and interaction.command.name == "say":
            await interaction.response.send_message(**kwargs)
        else:
            key = f"{interaction.user.id}:{interaction.command.name}"
            await interaction.client.rate_limiter.acquire(key)
            try:
                await interaction.response.send_message(**kwargs)
            finally:
                interaction.client.rate_limiter.release(key)
                
    except discord.errors.NotFound as e:
        logger.error(f"Interaction response failed (NotFound): {e}")
        try:
            await safe_followup_send(interaction, content=content or "❌ Error: Interaction expired.", embed=embed, file=file, view=view, ephemeral=ephemeral)
        except Exception as e2:
            logger.error(f"Followup send failed: {e2}")
            
    except discord.errors.HTTPException as e:
        if e.status == 429:  # Rate limit error
            retry_after = getattr(e, 'retry_after', 1)
            logger.warning(f"Rate limit hit, retrying after {retry_after}s")
            await asyncio.sleep(retry_after)
            
            # Reintento con backoff simple
            for attempt in range(3):  # Máximo 3 reintentos
                try:
                    if interaction.response.is_done():
                        await safe_followup_send(interaction, content=content, embed=embed, file=file, view=view, ephemeral=ephemeral)
                    else:
                        await interaction.response.send_message(**kwargs)
                    return
                except discord.errors.HTTPException as retry_e:
                    if retry_e.status == 429:
                        backoff = retry_after * (2 ** attempt)
                        logger.warning(f"Retry {attempt+1} failed, waiting {backoff}s")
                        await asyncio.sleep(backoff)
                    else:
                        raise
            logger.error("Max retries exceeded for rate limit")
        else:
            logger.error(f"HTTP error in safe_interaction_response: {e}")
            
    except Exception as e:
        logger.error(f"Error in safe_interaction_response: {e}")
        # Enviar respuesta de error si es posible
        try:
            if not interaction.response.is_done():
                await interaction.response.send_message("❌ Ocurrió un error al procesar el comando.", ephemeral=True)
        except Exception as fallback_error:
            logger.error(f"Fallback response failed: {fallback_error}")

async def safe_send_message(
    channel: discord.abc.Messageable, 
    content: Optional[str] = None, 
    embed: Optional[discord.Embed] = None,
    view: Optional[discord.ui.View] = None
):
    """
    Envía un mensaje con manejo de rate limits.
    """
    kwargs = {"content": content, "embed": embed}
    if view is not None:
        kwargs["view"] = view
    
    try:
        await channel.send(**kwargs)
    except discord.errors.HTTPException as e:
        if e.status == 429:
            retry_after = getattr(e, 'retry_after', 1)
            logger.warning(f"Rate limit hit on send_message, retrying after {retry_after}s")
            await asyncio.sleep(retry_after)
            await channel.send(**kwargs)
        else:
            logger.error(f"Error sending message: {e}")
            raise
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        raise

async def safe_followup_send(
    interaction: discord.Interaction, 
    content: Optional[str] = None, 
    embed: Optional[discord.Embed] = None, 
    file: Optional[Union[discord.File, list[discord.File]]] = None,
    view: Optional[discord.ui.View] = None,
    ephemeral: bool = False
):
    """
    Envía un followup message para slash commands con rate limit handling.
    """
    kwargs = {"content": content, "embed": embed, "ephemeral": ephemeral}
    if file is not None:
        kwargs["file"] = file
    if view is not None:
        kwargs["view"] = view
    
    try:
        await interaction.followup.send(**kwargs)
    except discord.errors.HTTPException as e:
        if e.status == 429:  # Rate limit
            retry_after = getattr(e, 'retry_after', 1)
            logger.warning(f"Rate limit hit on followup, retrying after {retry_after}s")
            await asyncio.sleep(retry_after)
            await interaction.followup.send(**kwargs)
        else:
            logger.error(f"HTTP error in safe_followup_send: {e}")
            raise
    except Exception as e:
        logger.error(f"Error in safe_followup_send: {e}")
        raise

async def safe_reply(
    message: discord.Message, 
    content: Optional[str] = None, 
    embed: Optional[discord.Embed] = None,
    view: Optional[discord.ui.View] = None
):
    """
    Envía una respuesta a un mensaje con rate limit handling.
    """
    kwargs = {"content": content, "embed": embed}
    if view is not None:
        kwargs["view"] = view
    
    try:
        await message.reply(**kwargs)
    except discord.errors.HTTPException as e:
        if e.status == 429:  # Rate limit
            retry_after = getattr(e, 'retry_after', 1)
            logger.warning(f"Rate limit hit on reply, retrying after {retry_after}s")
            await asyncio.sleep(retry_after)
            await message.reply(**kwargs)
        else:
            logger.error(f"HTTP error in safe_reply: {e}")
            raise
    except Exception as e:
        logger.error(f"Error in safe_reply: {e}")
        raise