import archives.models
import asyncio
import aiohttp
import datetime

qs = list(archives.models.TvSeriesModel.objects.all())

results = []


async def main():
    start = datetime.datetime.now()

    async with aiohttp.ClientSession() as session:
        for individual_season in qs:
            async with session.head(individual_season.imdb_url) as resp:
                pass

    finish = datetime.datetime.now()

    print(finish - start)

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
loop.close()
