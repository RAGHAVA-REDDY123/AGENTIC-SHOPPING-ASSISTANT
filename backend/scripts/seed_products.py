import sys
from decimal import Decimal
from typing import Any, Dict, List
from pathlib import Path

# Add project root to sys.path if executed directly as a script
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from backend.database.base import Base
from backend.database.connection import engine, get_db_session
from backend.models.product import Inventory, Product
from backend.schemas.product import ProductCreate
from backend.services.product_service import EmbeddingService

# Rich synthetic catalog dataset
SEED_CATALOG: List[Dict[str, Any]] = [
    # --- LAPTOPS ---
    {
        "name": "ASUS ROG Strix G15 Gaming Laptop",
        "slug": "asus-rog-strix-g15-gaming",
        "description": "High-performance gaming laptop equipped with next-gen ray tracing and high-refresh esports display.",
        "features": {
            "GPU": "NVIDIA RTX 4060 8GB",
            "CPU": "AMD Ryzen 9 7845HX",
            "RAM": "16GB DDR5 4800MHz",
            "Storage": "512GB NVMe M.2 SSD",
            "Display": '15.6" 144Hz IPS FHD Anti-Glare'
        },
        "specifications": {
            "OS": "Windows 11 Home",
            "WiFi": "WiFi 6E",
            "Bluetooth": "5.3",
            "Weight": "2.30 kg",
            "Battery": "90WHrs 4-cell Li-ion"
        },
        "price": Decimal("89999.00"),
        "original_price": Decimal("99999.00"),
        "discount_percent": 10,
        "brand": "ASUS",
        "category_slug": "laptops",
        "tags": ["gaming", "rtx", "high-performance", "ryzen", "esports"],
        "rating": Decimal("4.5"),
        "review_count": 1243,
        "image_url": "https://images.unsplash.com/photo-1603302576837-37561b2e2302",
        "initial_stock": 25,
    },
    {
        "name": "Apple MacBook Pro 14 M3",
        "slug": "apple-macbook-pro-14-m3",
        "description": "Pro-grade portable workstation featuring Apple Silicon M3 Pro chip and Liquid Retina XDR display.",
        "features": {
            "Chip": "Apple M3 Pro (11-core CPU, 14-core GPU)",
            "Memory": "18GB Unified Memory",
            "Storage": "512GB Superfast SSD",
            "Display": '14.2" Liquid Retina XDR 120Hz ProMotion'
        },
        "specifications": {
            "OS": "macOS Sonoma",
            "Ports": "3x Thunderbolt 4, HDMI, SDXC, MagSafe 3",
            "Weight": "1.61 kg",
            "BatteryLife": "Up to 18 hours"
        },
        "price": Decimal("199900.00"),
        "original_price": Decimal("219900.00"),
        "discount_percent": 9,
        "brand": "Apple",
        "category_slug": "laptops",
        "tags": ["macbook", "m3", "apple", "creator", "retina", "lightweight"],
        "rating": Decimal("4.9"),
        "review_count": 892,
        "image_url": "https://images.unsplash.com/photo-1517336714731-489689fd1ca8",
        "initial_stock": 18,
    },
    {
        "name": "Dell XPS 15 9530 Workstation",
        "slug": "dell-xps-15-9530-workstation",
        "description": "Premium ultrabook with edge-to-edge 3.5K OLED touchscreen and dedicated NVIDIA graphics.",
        "features": {
            "CPU": "Intel Core i7-13700H",
            "GPU": "NVIDIA GeForce RTX 4050 6GB",
            "RAM": "32GB DDR5",
            "Storage": "1TB PCIe NVMe SSD",
            "Display": '15.6" 3.5K OLED InfinityEdge Touch'
        },
        "specifications": {
            "OS": "Windows 11 Pro",
            "Chassis": "CNC Machined Aluminum & Carbon Fiber",
            "Weight": "1.92 kg"
        },
        "price": Decimal("174990.00"),
        "original_price": Decimal("189990.00"),
        "discount_percent": 8,
        "brand": "Dell",
        "category_slug": "laptops",
        "tags": ["ultrabook", "dell", "oled", "productivity", "professional"],
        "rating": Decimal("4.6"),
        "review_count": 431,
        "image_url": "https://images.unsplash.com/photo-1593642632823-8f785ba67e45",
        "initial_stock": 12,
    },
    {
        "name": "Lenovo Legion Pro 5i",
        "slug": "lenovo-legion-pro-5i",
        "description": "Engineered for intense esports battles with Coldfront 5.0 thermal technology.",
        "features": {
            "CPU": "Intel Core i9-14900HX",
            "GPU": "NVIDIA RTX 4070 8GB GDDR6",
            "RAM": "32GB DDR5 5600MHz",
            "Storage": "1TB SSD",
            "Display": '16" WQXGA 240Hz 500nits'
        },
        "specifications": {
            "OS": "Windows 11 Home",
            "Audio": "Nahimic Audio 2x 2W",
            "Weight": "2.55 kg"
        },
        "price": Decimal("148990.00"),
        "original_price": Decimal("165990.00"),
        "discount_percent": 10,
        "brand": "Lenovo",
        "category_slug": "laptops",
        "tags": ["gaming", "esports", "lenovo", "rtx4070", "high-refresh"],
        "rating": Decimal("4.7"),
        "review_count": 670,
        "image_url": "https://images.unsplash.com/photo-1588872657578-7efd1f1555ed",
        "initial_stock": 15,
    },
    {
        "name": "Apple MacBook Air 13 M2",
        "slug": "apple-macbook-air-13-m2",
        "description": "Ultra-thin, fanless silent laptop with stunning 13.6-inch Liquid Retina display.",
        "features": {
            "Chip": "Apple M2 8-core CPU",
            "Memory": "8GB Unified Memory",
            "Storage": "256GB SSD",
            "Display": '13.6" Liquid Retina Display'
        },
        "specifications": {
            "OS": "macOS Sonoma",
            "Weight": "1.24 kg",
            "BatteryLife": "Up to 18 hours",
            "MagSafe": "MagSafe 3 Charging"
        },
        "price": Decimal("94900.00"),
        "original_price": Decimal("99900.00"),
        "discount_percent": 5,
        "brand": "Apple",
        "category_slug": "laptops",
        "tags": ["macbook", "air", "lightweight", "students", "silent", "apple"],
        "rating": Decimal("4.8"),
        "review_count": 3120,
        "image_url": "https://images.unsplash.com/photo-1611186871348-b1ce696e52c9",
        "initial_stock": 35,
    },

    # --- MOBILES ---
    {
        "name": "Apple iPhone 15 Pro Max",
        "slug": "apple-iphone-15-pro-max",
        "description": "Aerospace-grade titanium design featuring the groundbreaking A17 Pro chip and 5x optical telephoto camera.",
        "features": {
            "SoC": "A17 Pro Chip",
            "Camera": "48MP Main + 12MP Ultra Wide + 12MP 5x Telephoto",
            "Display": '6.7" Super Retina XDR Always-On OLED',
            "Storage": "256GB"
        },
        "specifications": {
            "Build": "Grade 5 Titanium & Textured Matte Glass",
            "Connector": "USB-C with USB 3 speeds",
            "Weight": "221 g",
            "Resistance": "IP68 water and dust resistance"
        },
        "price": Decimal("149900.00"),
        "original_price": Decimal("159900.00"),
        "discount_percent": 6,
        "brand": "Apple",
        "category_slug": "mobiles",
        "tags": ["iphone", "apple", "5g", "camera", "titanium", "flagship"],
        "rating": Decimal("4.8"),
        "review_count": 4820,
        "image_url": "https://images.unsplash.com/photo-1592750475338-74b7b21085ab",
        "initial_stock": 40,
    },
    {
        "name": "Samsung Galaxy S24 Ultra",
        "slug": "samsung-galaxy-s24-ultra",
        "description": "Galaxy AI powerhouse with 200MP camera, built-in S-Pen, and flat Titanium frame.",
        "features": {
            "Processor": "Snapdragon 8 Gen 3 for Galaxy",
            "Camera": "200MP Quad Tele System with AI zoom",
            "Display": '6.8" QHD+ Dynamic AMOLED 2X 2600nits',
            "RAM": "12GB",
            "Storage": "256GB"
        },
        "specifications": {
            "S-Pen": "Integrated Bluetooth stylus",
            "Battery": "5000 mAh with 45W fast charging",
            "Protection": "Corning Gorilla Armor",
            "Weight": "232 g"
        },
        "price": Decimal("129999.00"),
        "original_price": Decimal("139999.00"),
        "discount_percent": 7,
        "brand": "Samsung",
        "category_slug": "mobiles",
        "tags": ["samsung", "galaxy", "flagship", "ai", "spen", "200mp", "android"],
        "rating": Decimal("4.7"),
        "review_count": 2980,
        "image_url": "https://images.unsplash.com/photo-1610945265064-0e34e5519bbf",
        "initial_stock": 30,
    },
    {
        "name": "Google Pixel 8 Pro",
        "slug": "google-pixel-8-pro",
        "description": "Everyday AI phone with Google Tensor G3, best-in-class computational photography and temperature sensor.",
        "features": {
            "Chip": "Google Tensor G3",
            "Camera": "50MP Main + 48MP Ultrawide + 48MP 5x Telephoto",
            "Display": '6.7" Super Actua Display 1-120Hz',
            "Storage": "128GB"
        },
        "specifications": {
            "OS": "Android 14 (7 years of OS updates)",
            "Sensors": "Thermometer, In-display fingerprint",
            "Battery": "5050 mAh"
        },
        "price": Decimal("97999.00"),
        "original_price": Decimal("106999.00"),
        "discount_percent": 8,
        "brand": "Google",
        "category_slug": "mobiles",
        "tags": ["google", "pixel", "pure-android", "ai", "camera", "tensor"],
        "rating": Decimal("4.6"),
        "review_count": 1450,
        "image_url": "https://images.unsplash.com/photo-1598327105666-5b89351aff97",
        "initial_stock": 20,
    },
    {
        "name": "OnePlus 12 5G",
        "slug": "oneplus-12-5g",
        "description": "Smooth Beyond Belief with 4th Gen Hasselblad Camera and 100W SuperVOOC ultra-fast charging.",
        "features": {
            "Processor": "Qualcomm Snapdragon 8 Gen 3",
            "Camera": "50MP Sony LYT-808 + 64MP 3x Periscope",
            "Display": '6.82" 2K 120Hz ProXDR with Aqua Touch',
            "RAM": "16GB LPDDR5X",
            "Storage": "512GB UFS 4.0"
        },
        "specifications": {
            "Charging": "100W wired, 50W AIRVOOC wireless",
            "Battery": "5400 mAh",
            "AlertSlider": "Physical 3-position alert slider"
        },
        "price": Decimal("69999.00"),
        "original_price": Decimal("74999.00"),
        "discount_percent": 7,
        "brand": "OnePlus",
        "category_slug": "mobiles",
        "tags": ["oneplus", "fast-charging", "snapdragon", "hasselblad", "5g"],
        "rating": Decimal("4.5"),
        "review_count": 2180,
        "image_url": "https://images.unsplash.com/photo-1511707171634-5f897ff02596",
        "initial_stock": 35,
    },
    {
        "name": "Samsung Galaxy Z Fold5",
        "slug": "samsung-galaxy-z-fold5",
        "description": "Ultimate multitasking foldable phone with zero-gap flex hinge and expansive 7.6-inch inner screen.",
        "features": {
            "MainScreen": '7.6" QXGA+ Dynamic AMOLED 2X 120Hz Foldable',
            "CoverScreen": '6.2" Dynamic AMOLED 2X',
            "Processor": "Snapdragon 8 Gen 3 for Galaxy",
            "Storage": "512GB"
        },
        "specifications": {
            "Hinge": "Dual rail Flex Hinge",
            "Waterproof": "IPX8 water resistant",
            "Weight": "253 g"
        },
        "price": Decimal("164999.00"),
        "original_price": Decimal("184999.00"),
        "discount_percent": 11,
        "brand": "Samsung",
        "category_slug": "mobiles",
        "tags": ["samsung", "foldable", "multitasking", "flagship", "large-screen"],
        "rating": Decimal("4.4"),
        "review_count": 890,
        "image_url": "https://images.unsplash.com/photo-1580910051074-3eb694886505",
        "initial_stock": 8,
    },

    # --- HEADPHONES & AUDIO ---
    {
        "name": "Sony WH-1000XM5 Wireless Headphones",
        "slug": "sony-wh-1000xm5-wireless",
        "description": "Industry-leading noise canceling headphones with dual processors and 8 microphones for unmatched clarity.",
        "features": {
            "NoiseCanceling": "Auto NC Optimizer with V1 & QN1 chips",
            "Driver": "30mm precision engineered carbon fiber driver",
            "Battery": "30 hours with ANC on (3 min quick charge = 3 hours)",
            "Codecs": "LDAC, AAC, SBC"
        },
        "specifications": {
            "Bluetooth": "5.2 with Multipoint Connection",
            "Weight": "250 g",
            "VoiceAssistant": "Google Assistant & Alexa built-in"
        },
        "price": Decimal("29990.00"),
        "original_price": Decimal("34990.00"),
        "discount_percent": 14,
        "brand": "Sony",
        "category_slug": "headphones",
        "tags": ["headphones", "sony", "anc", "wireless", "audiophile", "travel"],
        "rating": Decimal("4.7"),
        "review_count": 5210,
        "image_url": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e",
        "initial_stock": 50,
    },
    {
        "name": "Bose QuietComfort Ultra Headphones",
        "slug": "bose-quietcomfort-ultra-headphones",
        "description": "World-class active noise cancellation with groundbreaking Spatial Immersive Audio and CustomTune technology.",
        "features": {
            "Audio": "Bose Immersive Audio Spatial Experience",
            "NoiseCancellation": "Active Noise Cancelling with Quiet & Aware Modes",
            "Battery": "Up to 24 hours playback (18 hrs with Immersive)"
        },
        "specifications": {
            "Bluetooth": "5.3 with Snapdragon Sound aptX Adaptive",
            "Weight": "252 g",
            "Materials": "Luxurious protein leather ear cushions"
        },
        "price": Decimal("35900.00"),
        "original_price": Decimal("39900.00"),
        "discount_percent": 10,
        "brand": "Bose",
        "category_slug": "headphones",
        "tags": ["bose", "anc", "spatial-audio", "comfort", "travel", "headphones"],
        "rating": Decimal("4.8"),
        "review_count": 1820,
        "image_url": "https://images.unsplash.com/photo-1546435770-a3e426bf472b",
        "initial_stock": 22,
    },
    {
        "name": "Apple AirPods Pro 2nd Gen USB-C",
        "slug": "apple-airpods-pro-2nd-gen",
        "description": "Featuring the H2 chip, up to 2x more Active Noise Cancellation, Adaptive Audio, and USB-C MagSafe case.",
        "features": {
            "Chip": "Apple H2 headphone chip",
            "Audio": "Personalized Spatial Audio with dynamic head tracking",
            "Battery": "Up to 6 hours listening (30 hours total with case)"
        },
        "specifications": {
            "Connectivity": "Bluetooth 5.3",
            "Charging": "USB-C, MagSafe, Apple Watch charger",
            "Resistance": "IP54 dust, sweat, and water resistant"
        },
        "price": Decimal("24900.00"),
        "original_price": Decimal("26900.00"),
        "discount_percent": 7,
        "brand": "Apple",
        "category_slug": "headphones",
        "tags": ["airpods", "apple", "earbuds", "tws", "anc", "spatial-audio"],
        "rating": Decimal("4.8"),
        "review_count": 7800,
        "image_url": "https://images.unsplash.com/photo-1600294037681-c80b4cb5b434",
        "initial_stock": 60,
    },
    {
        "name": "Sennheiser Momentum 4 Wireless",
        "slug": "sennheiser-momentum-4-wireless",
        "description": "Audiophile-inspired 42mm transducer system boasting an unbelievable 60-hour battery life.",
        "features": {
            "Battery": "Unmatched 60-hour battery life",
            "Drivers": "Audiophile 42mm acoustic system",
            "ANC": "Adaptive Noise Cancellation & Transparency Mode"
        },
        "specifications": {
            "CodecSupport": "aptX Adaptive, aptX, AAC, SBC",
            "Microphones": "2x2 beamforming digital mic array",
            "Weight": "293 g"
        },
        "price": Decimal("27990.00"),
        "original_price": Decimal("34990.00"),
        "discount_percent": 20,
        "brand": "Sennheiser",
        "category_slug": "headphones",
        "tags": ["sennheiser", "audiophile", "long-battery", "wireless", "anc"],
        "rating": Decimal("4.6"),
        "review_count": 1120,
        "image_url": "https://images.unsplash.com/photo-1484704849700-f032a568e944",
        "initial_stock": 14,
    },
    {
        "name": "Sony WF-1000XM5 True Wireless Earbuds",
        "slug": "sony-wf-1000xm5-earbuds",
        "description": "Astonishing sound quality and the best noise canceling in compact true-wireless earbuds.",
        "features": {
            "ANC": "Integrated Processor V2 + HD Noise Cancelling Processor QN2e",
            "Drivers": "Dynamic Driver X (8.4mm)",
            "Battery": "8 hours (24 hours with case)"
        },
        "specifications": {
            "Codecs": "LDAC, AAC, SBC, LC3",
            "Waterproof": "IPX4",
            "Weight": "5.9 g per earbud"
        },
        "price": Decimal("23990.00"),
        "original_price": Decimal("29990.00"),
        "discount_percent": 20,
        "brand": "Sony",
        "category_slug": "headphones",
        "tags": ["sony", "earbuds", "tws", "anc", "ldac", "water-resistant"],
        "rating": Decimal("4.5"),
        "review_count": 2100,
        "image_url": "https://images.unsplash.com/photo-1590658268037-6bf12165a8df",
        "initial_stock": 28,
    },

    # --- ACCESSORIES & WEARABLES ---
    {
        "name": "Apple Watch Series 9 GPS 45mm",
        "slug": "apple-watch-series-9-45mm",
        "description": "Smarter, brighter, and mightier with the S9 chip, Double Tap gesture, and Blood Oxygen monitoring.",
        "features": {
            "Chip": "S9 SiP with 4-core Neural Engine",
            "Gestures": "Double tap gesture control",
            "Display": "Always-On Retina display up to 2000 nits",
            "Health": "Blood Oxygen, ECG, Temperature sensing, Cycle tracking"
        },
        "specifications": {
            "Size": "45mm Aluminum Case",
            "WaterResistance": "50m swimproof",
            "Battery": "18 hours normal, 36 hours low power mode"
        },
        "price": Decimal("44900.00"),
        "original_price": Decimal("47900.00"),
        "discount_percent": 6,
        "brand": "Apple",
        "category_slug": "accessories",
        "tags": ["smartwatch", "apple", "fitness", "health", "wearable", "accessories"],
        "rating": Decimal("4.8"),
        "review_count": 3410,
        "image_url": "https://images.unsplash.com/photo-1546868871-7041f2a55e12",
        "initial_stock": 30,
    },
    {
        "name": "Samsung Galaxy Watch6 Classic 47mm",
        "slug": "samsung-galaxy-watch6-classic-47mm",
        "description": "Timeless rotating bezel, comprehensive sleep coaching, and advanced BioActive health sensor.",
        "features": {
            "Hardware": "Physical rotating bezel & Sapphire Crystal glass",
            "Sensors": "Samsung BioActive Sensor (Optical Heart + ECG + BIA)",
            "Display": '1.5" Super AMOLED Always-on'
        },
        "specifications": {
            "OS": "Wear OS Powered by Samsung",
            "Durability": "5ATM + IP68 / MIL-STD-810H",
            "Battery": "425 mAh with fast wireless charging"
        },
        "price": Decimal("36999.00"),
        "original_price": Decimal("42999.00"),
        "discount_percent": 14,
        "brand": "Samsung",
        "category_slug": "accessories",
        "tags": ["smartwatch", "samsung", "wearos", "fitness", "rotating-bezel"],
        "rating": Decimal("4.6"),
        "review_count": 1420,
        "image_url": "https://images.unsplash.com/photo-1523275335684-37898b6baf30",
        "initial_stock": 25,
    },
    {
        "name": "Logitech MX Master 3S Wireless Mouse",
        "slug": "logitech-mx-master-3s",
        "description": "The ultimate precision productivity mouse with 8K DPI any-surface sensor and 90% quieter clicks.",
        "features": {
            "Sensor": "Darkfield 8000 DPI high precision (tracks on glass)",
            "Scroll": "MagSpeed Electromagnetic scrolling (1000 lines/sec)",
            "Buttons": "7 customizable buttons with gesture support"
        },
        "specifications": {
            "Battery": "500 mAh Li-Po (up to 70 days per charge)",
            "Connection": "Logi Bolt USB Receiver & Bluetooth Low Energy",
            "Weight": "141 g"
        },
        "price": Decimal("8995.00"),
        "original_price": Decimal("10995.00"),
        "discount_percent": 18,
        "brand": "Logitech",
        "category_slug": "accessories",
        "tags": ["mouse", "logitech", "ergonomic", "productivity", "wireless", "accessories"],
        "rating": Decimal("4.9"),
        "review_count": 9150,
        "image_url": "https://images.unsplash.com/photo-1615663245857-ac93bb7c39e7",
        "initial_stock": 45,
    },
    {
        "name": "Keychron Q1 Pro Wireless Mechanical Keyboard",
        "slug": "keychron-q1-pro-mechanical-keyboard",
        "description": "Fully customizable 75% QMK/VIA wireless mechanical keyboard with CNC aluminum body and hot-swappable switches.",
        "features": {
            "Layout": "75% compact exploded layout with rotary encoder knob",
            "Switches": "Keychron K Pro Red (Pre-lubed, Hot-swappable)",
            "Body": "Full CNC Machined Aluminum Frame"
        },
        "specifications": {
            "Connectivity": "Bluetooth 5.1 & Type-C Wired",
            "Compatibility": "macOS, Windows, Linux",
            "Battery": "4000 mAh rechargeable"
        },
        "price": Decimal("17999.00"),
        "original_price": Decimal("19999.00"),
        "discount_percent": 10,
        "brand": "Keychron",
        "category_slug": "accessories",
        "tags": ["keyboard", "mechanical", "custom", "qmk", "wireless", "accessories"],
        "rating": Decimal("4.8"),
        "review_count": 870,
        "image_url": "https://images.unsplash.com/photo-1587829741301-dc798b83add3",
        "initial_stock": 16,
    },
    {
        "name": "Anker Prime 20000mAh Power Bank 200W",
        "slug": "anker-prime-20000mah-power-bank",
        "description": "Ultra-fast multi-device fast charging power bank with 200W total output and real-time digital display.",
        "features": {
            "Output": "200W total output (100W single port max)",
            "Capacity": "20,000mAh airline approved",
            "Display": "Smart digital display showing watts, battery health, recharge time"
        },
        "specifications": {
            "Ports": "2x USB-C, 1x USB-A",
            "RechargeSpeed": "100W rapid recharge in 1 hour 15 min",
            "Weight": "540 g"
        },
        "price": Decimal("11999.00"),
        "original_price": Decimal("14999.00"),
        "discount_percent": 20,
        "brand": "Anker",
        "category_slug": "accessories",
        "tags": ["powerbank", "anker", "fast-charging", "travel", "accessories"],
        "rating": Decimal("4.7"),
        "review_count": 1640,
        "image_url": "https://images.unsplash.com/photo-1609592424368-23259858593a",
        "initial_stock": 35,
    },
    {
        "name": "Dell UltraSharp 27 4K USB-C Hub Monitor",
        "slug": "dell-ultrasharp-27-4k-u2723qe",
        "description": "Brilliant 27-inch 4K monitor with breakthrough IPS Black technology, 98% DCI-P3, and 90W USB-C power delivery.",
        "features": {
            "Panel": "27-inch 4K UHD (3840 x 2160) IPS Black with 2000:1 contrast",
            "Color": "100% sRGB, 100% Rec 709, 98% DCI-P3",
            "Hub": "USB-C Hub with RJ45 Ethernet and 90W Power Delivery"
        },
        "specifications": {
            "Stand": "Height adjustable, tilt, swivel, pivot",
            "Ports": "HDMI, DisplayPort 1.4, USB-C upstream, 5x USB 3.2 downstream",
            "Warranty": "3-Year Advanced Exchange Service"
        },
        "price": Decimal("52990.00"),
        "original_price": Decimal("59990.00"),
        "discount_percent": 12,
        "brand": "Dell",
        "category_slug": "accessories",
        "tags": ["monitor", "4k", "dell", "creator", "ips-black", "accessories"],
        "rating": Decimal("4.7"),
        "review_count": 820,
        "image_url": "https://images.unsplash.com/photo-1527443224154-c4a3942d3acf",
        "initial_stock": 10,
    },
]


from sqlalchemy import text


def seed_product_catalog(verbose: bool = True) -> Dict[str, int]:
    """
    Idempotent catalog seeder with pgvector dense semantic embeddings.
    1. Creates vector extension and database schema tables if not present.
    2. Computes 384-dimensional dense semantic vectors using sentence-transformers.
    3. Validates catalog records against Pydantic ProductCreate schema.
    4. Inserts or updates products by unique slug (including vector embeddings).
    5. Seeds or updates corresponding inventory stock.
    6. Commits inside an atomic database transaction.
    """
    if verbose:
        print("=" * 60)
        print("SEEDING PRODUCT CATALOG WITH HYBRID PGVECTOR EMBEDDINGS")
        print("=" * 60)

    # 1. Enable pgvector extension and create all database tables
    with get_db_session() as db:
        try:
            db.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            db.commit()
            if verbose:
                print("[OK] pgvector extension enabled.")
        except Exception as e:
            db.rollback()
            if verbose:
                print(f"[Note] pgvector extension creation skipped: {e}")

    Base.metadata.create_all(bind=engine)

    inserted_count = 0
    updated_count = 0
    inventory_count = 0
    embeddings_generated = 0

    if verbose:
        print("Generating dense semantic embeddings for catalog...")

    with get_db_session() as db:
        for raw_item in SEED_CATALOG:
            # Generate 384-dimensional embedding if not present
            if not raw_item.get("embedding"):
                text_to_embed = EmbeddingService.build_product_embedding_text(raw_item)
                raw_item["embedding"] = EmbeddingService.embed_text(text_to_embed)
                embeddings_generated += 1


            # 2. Strict validation via Pydantic
            validated = ProductCreate(**raw_item)
            item_data = validated.model_dump()
            initial_stock = item_data.pop("initial_stock", 10)

            slug = item_data["slug"]


            # 3. Check for existing record by unique slug
            existing = db.query(Product).filter(Product.slug == slug).first()

            if existing:
                # Update existing fields
                for k, v in item_data.items():
                    if hasattr(existing, k) and k not in ("id", "created_at"):
                        setattr(existing, k, v)
                product_obj = existing
                updated_count += 1
            else:
                product_obj = Product(**item_data)
                db.add(product_obj)
                inserted_count += 1

            # Flush to guarantee product_obj has an assigned primary key
            db.flush()

            # 4. Upsert corresponding inventory
            existing_inv = db.query(Inventory).filter(Inventory.product_id == product_obj.id).first()
            if existing_inv:
                existing_inv.stock_quantity = initial_stock
            else:
                inv = Inventory(
                    product_id=product_obj.id,
                    stock_quantity=initial_stock,
                    reserved_quantity=0,
                )
                db.add(inv)
            inventory_count += 1

    summary = {
        "total_records": len(SEED_CATALOG),
        "inserted": inserted_count,
        "updated": updated_count,
        "inventory_records": inventory_count,
    }

    if verbose:
        print(f"Products inserted : {inserted_count}")
        print(f"Products updated  : {updated_count}")
        print(f"Inventory seeded  : {inventory_count}")
        print(f"Vectors embedded  : {embeddings_generated}")
        print("Catalog seeding completed successfully!")
        print("=" * 60)

    return summary


if __name__ == "__main__":
    try:
        seed_product_catalog(verbose=True)
    except Exception as exc:
        print(f"Seeding failed: {exc}", file=sys.stderr)
        sys.exit(1)
