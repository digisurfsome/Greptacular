# Google Maps Lead Scraping -- Find Local Businesses at Scale

## What You'll Build

A Node.js script that scrapes Google Maps to find local service businesses that need help with their online presence. It searches by industry and city, filters for high-quality businesses without a web presence, and exports clean lead lists to XLSX. Two approaches covered: Google Places API (recommended, reliable) and Apify Google Maps Scraper (faster, handles pagination).

## Prerequisites

- Node.js 18+
- Google Cloud account with billing enabled (for Places API) OR Apify account (free tier: 100 actor runs/month)
- Basic command line familiarity

## Estimated Time

30-45 minutes for the Google Places API approach. 15-20 minutes for the Apify approach.

## Environment Variables

```
# Google Places API approach
GOOGLE_PLACES_API_KEY=your_api_key

# Apify approach (alternative)
APIFY_API_KEY=your_apify_api_key
```

---

## Step 0: Choose Your Approach

| | Google Places API | Apify Scraper |
|---|---|---|
| Cost | ~$0.03-0.05 per lead | ~$5/1000 results on paid plan |
| Speed | 1-2 leads/second | 10-50 leads/second |
| Reliability | Very high (official API) | High (maintained actor) |
| Setup | Google Cloud project | Apify account |
| Pagination | Manual (pagetoken) | Automatic |
| Data quality | Structured, consistent | Structured, consistent |
| Best for | Targeted, smaller batches | Large-scale scraping |

Recommendation: Start with Google Places API for precision. Switch to Apify when you need volume.

---

## Target Industries (15)

These are local service businesses most likely to need help with marketing and online presence:

```javascript
const INDUSTRIES = [
  'plumbing',
  'HVAC',
  'roofing',
  'electrical',
  'landscaping',
  'cleaning service',
  'painting',
  'fencing',
  'tree service',
  'pest control',
  'concrete',
  'handyman',
  'pressure washing',
  'garage door',
  'pool service'
];
```

## City Targeting (3 Tiers)

```javascript
const CITIES = {
  tier1: [
    'Houston TX', 'Dallas TX', 'Phoenix AZ', 'San Antonio TX', 'Jacksonville FL',
    'Charlotte NC', 'Nashville TN', 'Austin TX', 'Denver CO', 'Atlanta GA'
  ],
  tier2: [
    'Tampa FL', 'Raleigh NC', 'Orlando FL', 'San Diego CA', 'Las Vegas NV',
    'Kansas City MO', 'Sacramento CA', 'Salt Lake City UT', 'Birmingham AL', 'Richmond VA',
    'Tucson AZ', 'Boise ID', 'Knoxville TN', 'Greenville SC', 'Chattanooga TN',
    'Fort Worth TX', 'Omaha NE', 'Tulsa OK', 'Colorado Springs CO', 'Lexington KY'
  ],
  tier3: [
    'Savannah GA', 'Asheville NC', 'Wilmington NC', 'Pensacola FL', 'Huntsville AL',
    'Baton Rouge LA', 'Little Rock AR', 'Amarillo TX', 'Lubbock TX', 'Waco TX',
    'Lakeland FL', 'Daytona Beach FL', 'Myrtle Beach SC', 'Fayetteville AR', 'Springfield MO',
    'Tyler TX', 'Midland TX', 'Ocala FL', 'Panama City FL', 'Clarksville TN'
  ]
};
```

---

## Approach 1: Google Places API

### Step 1: Set Up Google Cloud

1. Go to https://console.cloud.google.com
2. Create a new project (or use existing)
3. Enable the **Places API (New)** at https://console.cloud.google.com/apis/library/places-backend.googleapis.com
4. Go to Credentials > Create Credentials > API Key
5. Restrict the key to Places API only
6. Enable billing (required for Places API -- you get $200/month free credit)

### Step 2: Initialize the Project

```bash
mkdir google-maps-scraper && cd google-maps-scraper
npm init -y
npm install axios xlsx dotenv
```

Create `.env`:

```
GOOGLE_PLACES_API_KEY=your_api_key_here
```

### Step 3: Build the Scraper

Create `scraper.js`:

```javascript
require('dotenv').config();
const axios = require('axios');
const XLSX = require('xlsx');
const fs = require('fs');
const path = require('path');

const API_KEY = process.env.GOOGLE_PLACES_API_KEY;
const BASE_URL = 'https://places.googleapis.com/v1/places:searchText';
const DETAILS_URL = 'https://places.googleapis.com/v1/places';

// Configuration
const MIN_RATING = 4.5;
const MIN_REVIEWS = 20;
const MAX_RESULTS_PER_QUERY = 20; // Google returns max 20 per request

// Rate limiting
const DELAY_MS = 200; // 200ms between requests
const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));

async function searchPlaces(query) {
  try {
    const response = await axios.post(BASE_URL, {
      textQuery: query,
      maxResultCount: MAX_RESULTS_PER_QUERY
    }, {
      headers: {
        'Content-Type': 'application/json',
        'X-Goog-Api-Key': API_KEY,
        'X-Goog-FieldMask': 'places.id,places.displayName,places.formattedAddress,places.rating,places.userRatingCount,places.websiteUri,places.nationalPhoneNumber,places.googleMapsUri,places.types'
      }
    });

    return response.data.places || [];
  } catch (error) {
    console.error(`Search error for "${query}":`, error.response?.data?.error?.message || error.message);
    return [];
  }
}

async function getPlaceDetails(placeId) {
  try {
    const response = await axios.get(`${DETAILS_URL}/${placeId}`, {
      headers: {
        'X-Goog-Api-Key': API_KEY,
        'X-Goog-FieldMask': 'id,displayName,formattedAddress,rating,userRatingCount,websiteUri,nationalPhoneNumber,internationalPhoneNumber,googleMapsUri,reviews,types,businessStatus'
      }
    });

    return response.data;
  } catch (error) {
    console.error(`Details error for ${placeId}:`, error.response?.data?.error?.message || error.message);
    return null;
  }
}

function filterBusiness(place) {
  const rating = place.rating || 0;
  const reviews = place.userRatingCount || 0;
  const hasPhone = !!place.nationalPhoneNumber;
  const hasWebsite = !!place.websiteUri;

  // Keep businesses with good ratings, enough reviews, and a phone number
  // Prioritize those WITHOUT a website (they need the most help)
  if (rating < MIN_RATING) return false;
  if (reviews < MIN_REVIEWS) return false;
  if (!hasPhone) return false;

  return true;
}

function formatLead(place, details, city, industry) {
  const reviews = details?.reviews || [];
  const topReviews = reviews.slice(0, 3);

  return {
    company_name: place.displayName?.text || '',
    owner_name: '', // Not available from Places API -- enrich later
    phone: place.nationalPhoneNumber || '',
    email: '', // Not available from Places API -- enrich later
    star_rating: place.rating || 0,
    num_reviews: place.userRatingCount || 0,
    city: city.split(' ')[0],
    state: city.split(' ').pop(),
    industry: industry,
    services: (place.types || []).join(', '),
    has_website: place.websiteUri ? 'Yes' : 'No',
    website: place.websiteUri || '',
    google_maps_url: place.googleMapsUri || '',
    review_1_author: topReviews[0]?.authorAttribution?.displayName || '',
    review_1_text: topReviews[0]?.text?.text || '',
    review_2_author: topReviews[1]?.authorAttribution?.displayName || '',
    review_2_text: topReviews[1]?.text?.text || '',
    review_3_author: topReviews[2]?.authorAttribution?.displayName || '',
    review_3_text: topReviews[2]?.text?.text || ''
  };
}

async function scrapeIndustryCity(industry, city) {
  const query = `${industry} in ${city}`;
  console.log(`Searching: ${query}`);

  const places = await searchPlaces(query);
  console.log(`  Found ${places.length} results`);

  const filtered = places.filter(filterBusiness);
  console.log(`  ${filtered.length} passed filters (${MIN_RATING}+ stars, ${MIN_REVIEWS}+ reviews, has phone)`);

  const leads = [];

  for (const place of filtered) {
    await sleep(DELAY_MS);
    const details = await getPlaceDetails(place.id);
    leads.push(formatLead(place, details, city, industry));
  }

  return leads;
}

async function run() {
  const industry = process.argv[2];
  const city = process.argv[3];
  const tier = process.argv[4]; // optional: 'tier1', 'tier2', 'tier3', 'all'

  if (!industry && !tier) {
    console.log('Usage:');
    console.log('  Single search: node scraper.js "plumbing" "Houston TX"');
    console.log('  By tier:       node scraper.js "plumbing" --tier tier1');
    console.log('  All:           node scraper.js --all');
    process.exit(1);
  }

  let allLeads = [];
  const timestamp = new Date().toISOString().split('T')[0];

  if (process.argv[2] === '--all') {
    // Scrape everything
    const INDUSTRIES = [
      'plumbing', 'HVAC', 'roofing', 'electrical', 'landscaping',
      'cleaning service', 'painting', 'fencing', 'tree service', 'pest control',
      'concrete', 'handyman', 'pressure washing', 'garage door', 'pool service'
    ];

    const CITIES_TIER1 = [
      'Houston TX', 'Dallas TX', 'Phoenix AZ', 'San Antonio TX', 'Jacksonville FL',
      'Charlotte NC', 'Nashville TN', 'Austin TX', 'Denver CO', 'Atlanta GA'
    ];

    for (const ind of INDUSTRIES) {
      for (const c of CITIES_TIER1) {
        const leads = await scrapeIndustryCity(ind, c);
        allLeads = allLeads.concat(leads);
        await sleep(1000); // Extra delay between searches
      }
    }

    saveToXLSX(allLeads, `leads_all_tier1_${timestamp}.xlsx`);
  } else if (tier) {
    // Not implemented in this snippet -- extend CITIES object and loop
    console.log('Tier-based scraping: extend this section with your city lists');
  } else {
    // Single industry + city
    allLeads = await scrapeIndustryCity(industry, city);
    const slug = `${city.replace(/\s+/g, '_').toLowerCase()}_${industry.replace(/\s+/g, '_').toLowerCase()}`;
    saveToXLSX(allLeads, `leads_${slug}_${timestamp}.xlsx`);
  }

  console.log(`\nTotal leads scraped: ${allLeads.length}`);
}

function saveToXLSX(leads, filename) {
  if (leads.length === 0) {
    console.log('No leads to save.');
    return;
  }

  const outputDir = path.join(__dirname, 'output');
  if (!fs.existsSync(outputDir)) fs.mkdirSync(outputDir);

  const filepath = path.join(outputDir, filename);
  const worksheet = XLSX.utils.json_to_sheet(leads);
  const workbook = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(workbook, worksheet, 'Leads');
  XLSX.writeFile(workbook, filepath);

  console.log(`Saved ${leads.length} leads to ${filepath}`);
}

run().catch(console.error);
```

### Step 4: Run It

```bash
# Single search
node scraper.js "plumbing" "Houston TX"

# Check output
ls output/
```

---

## Approach 2: Apify Google Maps Scraper

Faster and handles pagination automatically. Better for large-scale scraping.

### Step 1: Set Up Apify

1. Create an account at https://apify.com
2. Go to Settings > Integrations > API tokens
3. Create a new token and copy it

### Step 2: Initialize the Project

```bash
mkdir google-maps-apify && cd google-maps-apify
npm init -y
npm install apify-client xlsx dotenv
```

Create `.env`:

```
APIFY_API_KEY=your_apify_token_here
```

### Step 3: Build the Apify Scraper

Create `scraper-apify.js`:

```javascript
require('dotenv').config();
const { ApifyClient } = require('apify-client');
const XLSX = require('xlsx');
const fs = require('fs');
const path = require('path');

const client = new ApifyClient({ token: process.env.APIFY_API_KEY });

// Apify Google Maps Scraper actor
const ACTOR_ID = 'nwua9Gu5YrADL7ZDj'; // compass/Google-Maps-Scraper

async function scrapeGoogleMaps(industry, city, maxResults = 100) {
  console.log(`Scraping: ${industry} in ${city} (max ${maxResults} results)`);

  const run = await client.actor(ACTOR_ID).call({
    searchStringsArray: [`${industry} in ${city}`],
    maxCrawledPlacesPerSearch: maxResults,
    language: 'en',
    includeWebResults: false,
    includeReviews: true,
    maxReviews: 3,
    scrapeReviewerName: true,
    scrapeReviewerUrl: false
  });

  // Fetch results
  const { items } = await client.dataset(run.defaultDatasetId).listItems();
  return items;
}

function filterAndFormat(items, city, industry) {
  return items
    .filter(item => {
      const rating = item.totalScore || 0;
      const reviews = item.reviewsCount || 0;
      const hasPhone = !!item.phone;
      return rating >= 4.5 && reviews >= 20 && hasPhone;
    })
    .map(item => {
      const reviews = item.reviews || [];
      return {
        company_name: item.title || '',
        owner_name: '', // Enrich separately
        phone: item.phone || '',
        email: item.email || '', // Sometimes available
        star_rating: item.totalScore || 0,
        num_reviews: item.reviewsCount || 0,
        city: city.split(' ')[0],
        state: city.split(' ').pop(),
        industry: industry,
        services: (item.categories || []).join(', '),
        has_website: item.website ? 'Yes' : 'No',
        website: item.website || '',
        google_maps_url: item.url || '',
        review_1_author: reviews[0]?.name || '',
        review_1_text: reviews[0]?.text || '',
        review_2_author: reviews[1]?.name || '',
        review_2_text: reviews[1]?.text || '',
        review_3_author: reviews[2]?.name || '',
        review_3_text: reviews[2]?.text || ''
      };
    });
}

function saveToXLSX(leads, filename) {
  if (leads.length === 0) {
    console.log('No leads to save.');
    return;
  }

  const outputDir = path.join(__dirname, 'output');
  if (!fs.existsSync(outputDir)) fs.mkdirSync(outputDir);

  const filepath = path.join(outputDir, filename);
  const worksheet = XLSX.utils.json_to_sheet(leads);
  const workbook = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(workbook, worksheet, 'Leads');
  XLSX.writeFile(workbook, filepath);

  console.log(`Saved ${leads.length} leads to ${filepath}`);
}

async function run() {
  const industry = process.argv[2] || 'plumbing';
  const city = process.argv[3] || 'Houston TX';
  const maxResults = parseInt(process.argv[4] || '100');

  const items = await scrapeGoogleMaps(industry, city, maxResults);
  console.log(`Raw results: ${items.length}`);

  const leads = filterAndFormat(items, city, industry);
  console.log(`After filtering: ${leads.length}`);

  const timestamp = new Date().toISOString().split('T')[0];
  const slug = `${city.replace(/\s+/g, '_').toLowerCase()}_${industry.replace(/\s+/g, '_').toLowerCase()}`;
  saveToXLSX(leads, `leads_${slug}_${timestamp}.xlsx`);
}

run().catch(console.error);
```

### Step 4: Run It

```bash
node scraper-apify.js "plumbing" "Houston TX" 100
```

---

## Output Schema

Every lead in the XLSX file has these columns:

| Column | Description |
|---|---|
| company_name | Business name from Google Maps |
| owner_name | Owner name (blank -- enrich separately via LinkedIn or website) |
| phone | Phone number |
| email | Email (often blank -- enrich separately) |
| star_rating | Google rating (4.5+) |
| num_reviews | Number of Google reviews (20+) |
| city | City name |
| state | State abbreviation |
| industry | Industry searched |
| services | Google Maps categories/types |
| has_website | "Yes" or "No" |
| website | Website URL if available |
| google_maps_url | Direct link to Google Maps listing |
| review_1_author | First review author name |
| review_1_text | First review text |
| review_2_author | Second review author name |
| review_2_text | Second review text |
| review_3_author | Third review author name |
| review_3_text | Third review text |

File naming: `leads_{city}_{industry}_{date}.xlsx`

---

## Cost Estimates

### Google Places API

- Text Search: $0.032 per request (up to 20 results)
- Place Details: $0.017 per request
- Per lead (with details): ~$0.05
- 500 leads: ~$25
- You get $200/month free Google Cloud credit

### Apify

- Free tier: 100 actor runs/month (each run can return 100+ results)
- Paid: starts at $49/month for more capacity
- Per lead: ~$0.005-0.01 on paid plan
- 500 leads: ~$5

### Total for 500 Initial Leads

- Google Places API approach: $25-50 (covered by free credits)
- Apify approach: $5-10 on paid plan, possibly free on free tier

---

## Testing and Verification

1. **Test a single search**: Run `node scraper.js "plumbing" "Houston TX"` and verify you get results.

2. **Check the XLSX output**: Open the file in Excel/Google Sheets. Verify all columns are populated correctly.

3. **Validate filtering**: Confirm every lead has 4.5+ stars, 20+ reviews, and a phone number.

4. **Check for duplicates**: If you run the same search twice, verify the output doesn't contain duplicate businesses.

5. **Spot-check accuracy**: Pick 3 leads from the XLSX and search them on Google Maps manually. Verify the data matches.

6. **Test multiple industries**: Run 2-3 different industries in the same city and verify the results are different businesses.

7. **Test the review data**: Verify that review_1, review_2, review_3 contain actual review text (not empty).

---

## You're Done When

- You can run a single command and get an XLSX file with leads for any industry + city combination
- Every lead in the file has: company_name, phone, star_rating (4.5+), num_reviews (20+), google_maps_url
- The file includes the top 3 reviews with author names and text
- You've successfully scraped at least 3 different industry/city combinations
- The output directory has properly named files: `leads_{city}_{industry}_{date}.xlsx`
- You can explain the cost: approximately how much you'll spend for your target number of leads
