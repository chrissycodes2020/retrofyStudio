from real_impact_scraper import RealImpactScraper
scraper = RealImpactScraper()

# Get the catalogs data
url = "https://api.impact.com/Mediapartners/IRFNBGTHkmio2071858ZgWZVTuFxnuqxN1/Catalogs"
response = scraper.session.get(url)
data = response.json()

print("=== CATALOGS RESPONSE ===")
print("Total catalogs:", data.get('@total'))
print("Catalogs available:", len(data.get('Catalogs', [])))

# Show available catalogs
catalogs = data.get('Catalogs', [])
for i, catalog in enumerate(catalogs):
    print(f"\nCatalog {i+1}:")
    for key, value in catalog.items():
        print(f"  {key}: {value}")

# If we find TheRealReal catalog, try to get products from it
for catalog in catalogs:
    if 'realreal' in str(catalog).lower():
        print(f"\n🎯 Found TheRealReal catalog!")
        # Try to access products from this catalog
        catalog_id = catalog.get('Id') or catalog.get('CatalogId')
        if catalog_id:
            print(f"Trying to get products from catalog {catalog_id}...")
            products_url = f"https://api.impact.com/Mediapartners/IRFNBGTHkmio2071858ZgWZVTuFxnuqxN1/Catalogs/{catalog_id}/Items"
            products_response = scraper.session.get(products_url, params={'PageSize': 5})
            print(f"Products response: {products_response.status_code}")
            if products_response.status_code == 200:
                products_data = products_response.json()
                print("Products found:", products_data.get('@total'))
                if products_data.get('Items'):
                    print("Sample product keys:", list(products_data['Items'][0].keys()))