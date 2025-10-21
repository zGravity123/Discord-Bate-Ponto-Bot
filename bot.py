import discord
from discord.ext import commands, tasks
import os
import asyncio
import sys
import logging
import colorlog

def setup_logger():
    handler = colorlog.StreamHandler()
    formatter = colorlog.ColoredFormatter(
        '%(log_color)s[%(asctime)s] [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)
    logger = colorlog.getLogger()
    if not logger.handlers:
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

setup_logger()

BOT_TOKEN = "TOKEN_HERE"

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        logging.info("A carregar os cogs...")
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                try:
                    await self.load_extension(f'cogs.{filename[:-3]}')
                    logging.info(f"  -> Cog '{filename}' carregado com sucesso.")
                except Exception as e:
                    logging.error(f"  -> Falha ao carregar o cog '{filename}': {e}")
        try:
            synced = await self.tree.sync()
            logging.info(f"Sincronizados {len(synced)} comandos de barra.")
        except Exception as e:
            logging.error(f"Falha ao sincronizar comandos: {e}")

    async def on_ready(self):
        logging.info(f'Bot conectado como {self.user.name} ({self.user.id})')
        logging.info('------')
        logging.info(">>> Bot operacional. Digite 'shutdown' ou 'restart' para gerir. <<<")
        
        activity = discord.Streaming(name="AuroraMC", url="https://www.twitch.tv/aurora")
        await self.change_presence(status=discord.Status.online, activity=activity)

bot = MyBot()

async def terminal_input_loop():
    while True:
        command = await asyncio.to_thread(sys.stdin.readline)
        command_parts = command.strip().split()
        if not command_parts: continue
        base_command = command_parts[0].lower()

        if base_command == "shutdown":
            logging.warning("Comando 'shutdown' recebido. A encerrar...")
            await bot.close()
            break
        elif base_command == "restart":
            logging.warning("Comando 'restart' recebido. A reiniciar...")
            await bot.close()
            os.execv(sys.executable, ['python'] + sys.argv)
        
        elif base_command == "teste":
            if len(command_parts) < 2:
                logging.error("Uso incorreto. Use: teste <ID_DO_UTILIZADOR>")
            else:
                try:
                    user_id = int(command_parts[1])
                    welcome_cog = bot.get_cog("Welcome")
                    if welcome_cog:
                        await welcome_cog.send_welcome_message(user_id)
                    else:
                        logging.error("O cog 'Welcome' não foi carregado. A mensagem de teste não pode ser enviada.")
                except ValueError:
                    logging.error(f"ID de utilizador inválido: '{command_parts[1]}'.")

async def main():
    asyncio.create_task(terminal_input_loop())
    await bot.start(BOT_TOKEN)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.warning("Bot desligado manualmente com Ctrl+C.")
