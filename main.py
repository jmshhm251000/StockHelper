import asyncio
from manage import main

if __name__ == "__main__":
    company_ticker = "mstr"
    asyncio.run(main(company_ticker))