"""
String Session Generator for Telegram Userbot.

Run this script once to generate a StringSession for your account.
The generated string is stored in OWNER_SESSION env variable.

Usage:
    python generate_session.py
"""

import asyncio
import sys
from telethon import TelegramClient
from telethon.sessions import StringSession


async def generate():
    print("=" * 60)
    print("  Telegram String Session Generator")
    print("=" * 60)
    print()

    try:
        api_id = int(input("Masukkan API_ID: ").strip())
        api_hash = input("Masukkan API_HASH: ").strip()
    except ValueError:
        print("[ERROR] API_ID harus berupa angka.")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n[INFO] Dibatalkan.")
        sys.exit(0)

    print()
    print("[INFO] Membuat sesi Telegram...")
    print("[INFO] Anda akan diminta memasukkan nomor telepon dan kode OTP.")
    print()

    async with TelegramClient(StringSession(), api_id, api_hash) as client:
        session_string = client.session.save()

    print()
    print("=" * 60)
    print("  ✅ STRING SESSION BERHASIL DIBUAT")
    print("=" * 60)
    print()
    print("Salin string berikut ke OWNER_SESSION di file .env:")
    print()
    print(session_string)
    print()
    print("=" * 60)
    print("[PENTING] Jaga kerahasiaan string session ini!")
    print("[PENTING] Jangan bagikan ke siapapun!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(generate())
