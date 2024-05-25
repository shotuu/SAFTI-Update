from telethon.sync import TelegramClient

api_id = '26298912'  # Replace with your API ID
api_hash = '05df5ce87f4dbe7f8c22dfda3e933bb8'  # Replace with your API hash

with TelegramClient('new', api_id, api_hash) as client:
    for dialog in client.iter_dialogs():
        if 'NAWS' or 'Lightning' in dialog.name:
            print(dialog.name, 'has ID', dialog.id)

# Army NAWS
# source_channel = -1001926733280

# Lightning Risk
# source_ channel = -1001347020644

# Test Channel
#source_channel = -1002005316137