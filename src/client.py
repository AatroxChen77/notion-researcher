import logging
from typing import List, Dict, Any, Tuple
from notion_client import Client
from src.parser import parse_markdown_to_blocks

logger = logging.getLogger(__name__)

class NotionSync:
    def __init__(self, token: str, root_page_id: str):
        """
        Initialize Notion Client.
        
        Args:
            token: Notion API Integration Token.
            root_page_id: The ID of the parent page to create children under.
        """
        self.token = token
        self.root_page_id = root_page_id
        
        try:
            self.client = Client(auth=self.token)
            logger.info("Notion Client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Notion Client: {e}")
            raise

    def create_child_page(self, title: str) -> Tuple[str, str]:
        """
        Creates a new child page under the root page.
        Returns: (new_page_id, new_page_url)
        """
        logger.info(f"Creating new child page: '{title}' under {self.root_page_id}...")
        try:
            parent = {"page_id": self.root_page_id}
            properties = {
                "title": [
                    {
                        "text": {
                            "content": title
                        }
                    }
                ]
            }
            response = self.client.pages.create(parent=parent, properties=properties)
            new_page_id = response["id"]
            new_page_url = response["url"]
            logger.info(f"✅ Child page created! ID: {new_page_id}")
            return new_page_id, new_page_url
        except Exception as e:
            logger.error(f"Failed to create child page: {e}")
            raise

    def push_blocks(self, page_id: str, blocks: List[Dict[str, Any]]):
        """
        Appends blocks to the specified page in batches of 100 (Notion API limit).
        """
        BATCH_SIZE = 100
        total_blocks = len(blocks)
        logger.info(f"Pushing {total_blocks} blocks to page {page_id}...")
        
        for i in range(0, total_blocks, BATCH_SIZE):
            batch = blocks[i : i + BATCH_SIZE]
            try:
                self.client.blocks.children.append(block_id=page_id, children=batch)
                logger.info(f"   - Batch {i//BATCH_SIZE + 1} pushed ({len(batch)} blocks)")
            except Exception as e:
                logger.error(f"❌ Failed to push batch starting at index {i}: {e}")
                # We continue trying other batches or raise? 
                # Usually better to stop to maintain order.
                raise
        
        logger.info("Push completed successfully!")
