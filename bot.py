from discord.ext import tasks
import os
from dotenv import load_dotenv
import discord
from discord.ext import commands
import requests
from bs4 import BeautifulSoup

load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')

intent = discord.Intents.default()
intent.members = True
intent.message_content = True

bot = commands.Bot(command_prefix='!', intents=intent)

search_terms = set()
online_channel_id = int(os.getenv('CHANNEL_ID'))
sent_links = set()  # store the links of the items already sent


@bot.event
async def on_ready():
    online_channel = bot.get_channel(online_channel_id)
    await online_channel.send(f'{bot.user} has connected to Discord!')
    print(f'{bot.user} has connected to Discord!')
    scrape.start()  # start the scraping task when the bot is ready


@bot.command(name='add')
async def add_term(ctx, *, term: str):
    print(f"Add command received with term: {term}")
    search_terms.add(term)
    await ctx.send(f"Added '{term}' to the search terms.")


@bot.command(name='remove')
async def remove_term(ctx, *, term: str):
    if term in search_terms:
        search_terms.remove(term)
        await ctx.send(f"Removed '{term}' from the search terms.")
    else:
        await ctx.send(f"Couldn't find '{term}' in the search terms.")


@bot.command(name='list')
async def list_terms(ctx):
    if not search_terms:
        await ctx.send("No search terms found.")
    else:
        terms = ', '.join(search_terms)
        await ctx.send(f"Current search terms: {terms}")


@tasks.loop(hours=1)
async def scrape():
    channel = bot.get_channel(online_channel_id)
    print(f"Scraping with search terms: {search_terms}")
    for term in search_terms:
        term_url = term.replace(' ', '+')
        url = f'https://www.ebay.com/sch/i.html?_nkw={term_url}&_sacat=0'
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        item_list = soup.find('ul', {'class': 'srp-results srp-grid clearfix'})

        if item_list is not None:
            items = item_list.find_all(
                'li', {'class': ['s-item', 'srp-river-answer srp-river-answer--REWRITE_START']})

            for item in items:
                stop_class = item.find(
                    'section', {'class': 'section-notice section-notice--information s-message HEADER'})
                if stop_class is not None:
                    break
                title = None
                price = None
                link = None
                title_div = item.find('div', {'class': 's-item__title'})
                if title_div is not None:
                    title = title_div.find('span')
                price = item.find('span', {'class': 's-item__price'})
                link = item.find('a', {'class': 's-item__link'})
                if title and price and link:
                    if link['href'] not in sent_links:
                        sent_links.add(link['href'])
                        await channel.send(f"{title.text}\n{price.text}\n{link['href']}")
        else:
            await channel.send(f"No items found for search term: {term}")


@bot.command(name='manual_scrape')
async def manual_scrape(ctx):
    await ctx.send("Running manual scrape...")
    await scrape()

bot.run(TOKEN)
