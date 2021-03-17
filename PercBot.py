import os
import discord
import pickle
import re
from datetime import datetime, timedelta
import asyncio
import json
import requests
import yfinance as yf


token = os.getenv("TOKEN")

client = discord.Client()


@client.event
async def on_ready():
    print("Logged in as " + str(client.user))


@client.event
async def on_message(msg):
    if msg.author == client.user:
        return
    elif msg.content.lower().startswith("-pk "):
        await MessageHandler(msg)
    elif msg.content.lower().startswith("-end"):
        await msg.channel.send("PercBot has been terminated")


async def MessageHandler(msg):
    with open("key.json", "r") as f:
        j = json.loads(f.read())
    content = msg.content.split()
    command = content[1].lower()

    if content[1] in j:
        await msg.channel.send(j[content[1]])
    elif command == "-timer":
        await MakeTimer(msg, int(content[2]), content[3:])

    elif command == "-addimage":
        try:
            imageAdder(msg)
        except Exception:
            await msg.channel.send("Could not make image")

    elif command == "-image":
        key = content[2]
        with open("Assets.json", "r") as f:
            j = json.loads(f.read())
        await msg.channel.send(file=discord.File(j[key]))
    elif command == "-t":
        await StockPriceHandler(msg)


def imageAdder(msg):
    key = msg.content.split(" ")[2]
    URL = msg.content.split(" ")[3]

    slugs = [".png", ".jpg", ".gif"]

    for s in slugs:
        if URL.lower().endswith(s):
            slug = s

    try:
        ImageResponse = requests.get(URL)
    except Exception as e:
        print(e)
        return
    with open(f"Assets/{key}{slug}", "wb") as f:
        f.write(ImageResponse.content)
    with open("Assets.json", "r") as f:
        js = json.loads(f.read())
        js[key] = f"Assets/{key}{slug}"
    with open("Assets.json", "w") as f:
        f.write(json.dumps(js))


async def StockPriceHandler(msg):
    content = msg.content.split(" ")
    ticker = content[2].upper()

    try:
        tickerInfo = yf.Ticker(ticker).info
    except KeyError:
        await msg.channel.send("Could not find ticker symbol")
        return
    price = tickerInfo["ask"]
    company = tickerInfo["longName"]
    info = ""
    if len(content) > 3:
        info = TickerMetricFormater(tickerInfo, content[3:])

    await msg.channel.send("{}: ${:,.2f}".format(company, price) + f"{info}")


def TickerMetricFormater(tickerInfo, metrics):
    commandHash = {
        "MARKET_CAP": "marketCap",
        "PE": "trailingPE",
        "DIVIDEND": "dividendRate"}
    percentage_metrics = ["DIVIDEND"]

    currency_metrics = ["MARKET_CAP"]
    extraInfo = []
    for command in metrics:
        if command.upper() in commandHash:
            if command.upper() in percentage_metrics:
                extraInfo.append("{}: {}%\n".format(
                    command.upper(), tickerInfo[commandHash[command.upper()]]))
            elif command.upper() in currency_metrics:
                extraInfo.append("{}: ${:,.2f}\n".format(
                    command.upper(), tickerInfo[commandHash[command.upper()]]))
            else:
                extraInfo.append("{}: {}\n".format(
                    command.upper(), tickerInfo[commandHash[command.upper()]]))

    info = "\n" + "".join(extraInfo)
    return info


async def MakeTimer(message, time, endMessage):
    await message.channel.send(f"Timer set for {time} minutes")
    await asyncio.sleep(60 * time)
    await message.channel.send(" ".join(endMessage))


client.run(token)
