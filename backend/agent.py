"""
AC Finder Agent - Searches for best BTU air conditioners from Singer and Abans
Uses OpenAI API for intelligent product analysis and comparison
"""

import requests
from bs4 import BeautifulSoup
import json
import re
from openai import OpenAI
import os
from datetime import datetime

class ACFinderAgent:
    def __init__(self, api_key, target_btu=None):
        """
        Initialize the AC Finder Agent
        
        Args:
            api_key: OpenAI API key
            target_btu: Target BTU value to search for (e.g., 12000, 18000)
        """
        self.client = OpenAI(api_key=api_key)
        self.target_btu = target_btu
        self.products = []
        
    def scrape_singer(self):
        """Scrape Singer website for AC products"""
        url = "https://www.singersl.com/products/appliances/air-conditioner"
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            }
            response = requests.get(url, headers=headers, timeout=20)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find product containers based on debug findings
            # Look for common product wrappers
            products = soup.select('.product, .productfilter, .views-row')
            
            for product in products:
                try:
                    name = ""
                    # Prioritize finding the image with alt text as it contains the full product name
                    img_elem = product.select_one('img[alt]')
                    if img_elem:
                         name = img_elem.get('alt', '').strip()
                    
                    if not name:
                        name_elem = product.select_one('.product-name, .title, h3, h4, a')
                        if name_elem:
                            name = name_elem.text.strip()
                    
                    if not name:
                         continue

                    # Extract BTU from product name
                    btu_match = re.search(r'(\d+)\s*BTU', name, re.IGNORECASE)
                    btu = int(btu_match.group(1)) if btu_match else None
                    
                    # Extract price
                    price_elem = product.select_one('.price, .product-price, .amount, .sell-price')
                    price = price_elem.text.strip() if price_elem else 'N/A'
                    
                    # Only add if it looks like an AC
                    if btu or 'AIR CONDITIONER' in name.upper():
                        self.products.append({
                            'brand': 'Singer',
                            'name': name,
                            'btu': btu,
                            'price': price,
                            'url': url
                        })
                except Exception as e:
                    continue
                    
            print(f"✓ Found {len([p for p in self.products if p['brand'] == 'Singer'])} Singer products")
            
        except Exception as e:
            print(f"✗ Error scraping Singer: {e}")
    
    def scrape_abans(self):
        """Scrape Abans website for AC products"""
        url = "https://buyabans.com/home-appliance/air-conditioners"
        
        try:
            # Abans seems to load products dynamically. This simple request might fail to get products.
            # We'll try to get the initial HTML, but it might be empty of products.
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            }
            response = requests.get(url, headers=headers, timeout=20)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Abans uses col-lg-3 for grid items usually
            products = soup.select('.product-card, .col-lg-3, .product-item')
            
            found_count = 0
            for product in products:
                try:
                    name_elem = product.select_one('.pro-name-compact, .pro-name, h4 a, .product-name')
                    name = name_elem.text.strip() if name_elem else ''
                    
                    if not name:
                        continue
                    
                    # Extract BTU
                    btu_match = re.search(r'(\d+)\s*BTU', name, re.IGNORECASE)
                    btu = int(btu_match.group(1)) if btu_match else None
                    
                    # Extract price
                    price_elem = product.select_one('.price-new, .selling-price, .price, .sale-price')
                    price = price_elem.text.strip() if price_elem else 'N/A'
                    
                    self.products.append({
                        'brand': 'Abans',
                        'name': name,
                        'btu': btu,
                        'price': price,
                        'url': url
                    })
                    found_count += 1
                except Exception as e:
                    continue
            
            if found_count == 0:
                 print("ℹ️  Abans website structure might be dynamic. Trying fallback search...")
                 # Fallback: scrape from search page if possible or note limitation
                 
            print(f"✓ Found {found_count} Abans products")
            
        except Exception as e:
            print(f"✗ Error scraping Abans: {e}")
    
    def analyze_with_ai(self, products_list):
        """Use OpenAI to analyze and compare products"""
        
        products_text = "\n".join([
            f"- {p['brand']}: {p['name']} | BTU: {p['btu']} | Price: {p['price']}"
            for p in products_list
        ])
        
        if not products_text:
             return "No products found to analyze."

        prompt = f"""Analyze these air conditioner products and provide:
1. Best value for money
2. Most energy efficient options
3. Recommendations based on BTU capacity
4. Price comparison between brands

Products:
{products_text}

Provide a concise analysis and recommendation."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert in air conditioning systems and consumer electronics."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"AI analysis failed: {e}"
    
    def find_matching_btu(self):
        """Find products matching target BTU"""
        if not self.target_btu:
            return self.products
        
        # Find exact matches and close matches (within 2000 BTU)
        matches = []
        for product in self.products:
            # If product has no BTU extracted, we might still want to list it if it mentions 'Air Conditioner'
            p_btu = product.get('btu')
            
            if p_btu:
                if p_btu == self.target_btu:
                    product['match_type'] = 'exact'
                    matches.append(product)
                elif abs(p_btu - self.target_btu) <= 2000:
                    product['match_type'] = 'close'
                    matches.append(product)
            else:
                # Include products where BTU wasn't parsed but might be relevant
                # especially if user input matches part of the name
                if str(self.target_btu) in product['name']:
                     product['match_type'] = 'possible'
                     matches.append(product)
        
        return matches
    
    def send_notification(self, message):
        """Print notification (can be extended to email/SMS)"""
        print("\n" + "="*60)
        print("🔔 NOTIFICATION")
        print("="*60)
        print(message)
        print("="*60)
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60 + "\n")
    
    def run(self):
        """Main execution method"""
        print("\n🤖 AC Finder Agent Starting...")
        
        # Scrape both websites
        print("📡 Scraping websites...")
        self.scrape_singer()
        self.scrape_abans()
        
        # Find matching products
        if self.target_btu:
            print(f"\n🔍 Searching for {self.target_btu} BTU...")
            matches = self.find_matching_btu()
            
            if matches:
                notification = f"Found {len(matches)} AC(s) matching {self.target_btu} BTU!\n\n"
                
                for product in matches:
                    notification += f"• {product['brand']} - {product['name']}\n"
                    notification += f"  BTU: {product['btu']} ({product['match_type']} match)\n"
                    notification += f"  Price: {product['price']}\n\n"
                
                self.send_notification(notification)
                
                # AI Analysis
                print("\n🧠 AI Analysis:")
                print("-" * 60)
                analysis = self.analyze_with_ai(matches)
                print(analysis)
                
            else:
                self.send_notification(f"No products found matching {self.target_btu} BTU")
        else:
            # Show all products with AI analysis
            print(f"\n📊 Total products found: {len(self.products)}")
            
            if self.products:
                print("\n🧠 AI Analysis:")
                print("-" * 60)
                analysis = self.analyze_with_ai(self.products)
                print(analysis)
        
        # Save results
        self.save_results()
    
    def save_results(self):
        """Save results to JSON file"""
        filename = f"ac_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filename, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'target_btu': self.target_btu,
                'total_products': len(self.products),
                'products': self.products
            }, f, indent=2)
        
        print(f"\n💾 Results saved to: {filename}")


# Example usage
if __name__ == "__main__":
    # Set your OpenAI API key
    API_KEY = os.getenv('OPENAI_API_KEY') or 'your-api-key-here'
    
    print("-" * 40)
    print("AC Finder Agent - Manual Input Mode")
    print("-" * 40)
    
    try:
        user_input = input("Enter target BTU (e.g., 12000) or press Enter for all: ").strip()
        if user_input:
            TARGET_BTU = int(user_input)
        else:
            TARGET_BTU = None
    except ValueError:
        print("Invalid input. Defaulting to searching all products.")
        TARGET_BTU = None
    
    # Create and run agent
    agent = ACFinderAgent(api_key=API_KEY, target_btu=TARGET_BTU)
    agent.run()