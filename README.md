# book-sync

Synchronize finished audiobooks from [Audiobookshelf](https://www.audiobookshelf.org/) to [Grist](https://www.getgrist.com/).

## Features

- **Incremental syncs** - State management ensures only new audiobooks are synced, avoiding duplicates
- **Multi-language support** - Handle books written and read in different languages
- **Track multiple reads** - Record each time a book is read or re-read

## Usage

1. Import the Grist base from `grist/Books Tracker.grist` into your Grist workspace
2. Configure environment variables for Audiobookshelf and Grist API access
3. Run the sync command to import completed audiobooks:

```bash
book-sync
```
