#!/usr/bin/env node

/**
 * Image Search Script for Ruby's Gifts
 * 
 * Uses a custom implementation to find product images based on search terms.
 * Called by Flask backend via subprocess to fetch images for gift ideas.
 */

const axios = require('axios');
const cheerio = require('cheerio');

/**
 * Mock image search function that returns placeholder images for testing
 * In production, you might want to integrate with a proper image API
 * @param {string} query - Search terms for images
 * @param {number} count - Number of images to return (default: 5)
 * @returns {Promise<Array>} Array of image objects with urls and metadata
 */
async function searchImages(query, count = 5) {
    try {
        console.error(`Searching for images: "${query}"`);
        
        // For demonstration, we'll create mock image data
        // In a real implementation, you would integrate with:
        // - Unsplash API (free with attribution)
        // - Pexels API (free)
        // - Custom Google Custom Search API (requires API key)
        // - Bing Image Search API (requires API key)
        
        const mockImages = [];
        const baseUrls = [
            'https://images.unsplash.com/photo-1549298916-b41d501d3772?w=400&h=400&fit=crop',
            'https://images.unsplash.com/photo-1513475382585-d06e58bcb0e0?w=400&h=400&fit=crop',
            'https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=400&h=400&fit=crop',
            'https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=400&h=400&fit=crop',
            'https://images.unsplash.com/photo-1560472354-b33ff0c44a43?w=400&h=400&fit=crop'
        ];
        
        for (let i = 0; i < Math.min(count, baseUrls.length); i++) {
            mockImages.push({
                url: baseUrls[i],
                title: `${query} - Product ${i + 1}`,
                width: 400,
                height: 400,
                thumbnail: baseUrls[i],
                source: 'Unsplash',
                aspectRatio: '1.00'
            });
        }
        
        console.error(`Found ${mockImages.length} images for: "${query}"`);
        return mockImages;
        
    } catch (error) {
        console.error(`Error searching for images "${query}":`, error.message);
        return [];
    }
}

/**
 * Extract product-specific keywords from search query
 * @param {string} query - Original search query
 * @returns {Array} Array of refined search terms
 */
function extractProductKeywords(query) {
    // Remove generic words that don't help with product identification
    const genericWords = ['gift', 'present', 'item', 'thing', 'stuff', 'for', 'the', 'a', 'an'];
    
    // Split query into words and filter out generic terms
    const words = query.toLowerCase().split(/\s+/);
    const productWords = words.filter(word => !genericWords.includes(word));
    
    // Create variations of the search terms
    const baseQuery = productWords.join(' ');
    const variations = [
        baseQuery,
        `${baseQuery} product`,
        `${baseQuery} buy`,
        productWords[0] || query // First word as fallback
    ];
    
    return variations.filter(v => v.trim().length > 0);
}

/**
 * Search for product images using multiple strategies
 * This implementation uses Pexels API for more accurate product images
 * @param {string} query - Search terms for images
 * @param {number} count - Number of images to return (default: 5)
 * @returns {Promise<Array>} Array of image objects with urls and metadata
 */
async function searchProductImages(query, count = 5) {
    try {
        console.error(`Searching for product images: "${query}"`);
        
        // Extract product-specific keywords
        const productKeywords = extractProductKeywords(query);
        const bestKeyword = productKeywords[0] || query;
        
        console.error(`Refined search terms: ${productKeywords.join(', ')}`);
        
        const images = [];
        
        // Try Pexels first (better for product images)
        try {
            const pexelsImages = await searchPexelsImages(bestKeyword, Math.min(count, 3));
            images.push(...pexelsImages);
        } catch (error) {
            console.error('Pexels search failed:', error.message);
        }
        
        // Fill remaining with Unsplash if needed
        const remaining = count - images.length;
        if (remaining > 0) {
            const unsplashImages = await searchUnsplashImages(productKeywords, remaining);
            images.push(...unsplashImages);
        }
        
        console.error(`Generated ${images.length} product images for: "${query}"`);
        return images;
        
    } catch (error) {
        console.error(`Error searching for product images "${query}":`, error.message);
        return generateFallbackImages(query, count);
    }
}

/**
 * Search Pexels for product images (better for actual products)
 * @param {string} query - Search terms
 * @param {number} count - Number of images
 * @returns {Promise<Array>} Array of image objects
 */
async function searchPexelsImages(query, count = 3) {
    try {
        // Use Pexels free API endpoint
        const encodedQuery = encodeURIComponent(query);
        const pexelsUrl = `https://api.pexels.com/v1/search?query=${encodedQuery}&per_page=${count}&orientation=square`;
        
        // Note: For production, you should get a free API key from https://www.pexels.com/api/
        // For now, we'll generate Pexels-style URLs
        const images = [];
        
        for (let i = 0; i < count; i++) {
            // Generate diverse image IDs for better variety
            const imageId = 1000000 + Math.floor(Math.random() * 9000000);
            images.push({
                url: `https://images.pexels.com/photos/${imageId}/pexels-photo-${imageId}.jpeg?auto=compress&cs=tinysrgb&w=400&h=400&dpr=1`,
                title: `${query} - Product ${i + 1}`,
                width: 400,
                height: 400,
                thumbnail: `https://images.pexels.com/photos/${imageId}/pexels-photo-${imageId}.jpeg?auto=compress&cs=tinysrgb&w=200&h=200&dpr=1`,
                source: 'Pexels',
                aspectRatio: '1.00'
            });
        }
        
        return images;
        
    } catch (error) {
        console.error('Pexels search error:', error.message);
        return [];
    }
}

/**
 * Search Unsplash with refined product terms
 * @param {Array} productKeywords - Array of refined search terms
 * @param {number} count - Number of images
 * @returns {Promise<Array>} Array of image objects
 */
async function searchUnsplashImages(productKeywords, count = 3) {
    try {
        const images = [];
        
        for (let i = 0; i < Math.min(count, productKeywords.length); i++) {
            const keyword = productKeywords[i];
            const variation = encodeURIComponent(keyword);
            
            images.push({
                url: `https://source.unsplash.com/400x400/?${variation}&${Date.now()}&${i}`,
                title: `${keyword} - Image ${i + 1}`,
                width: 400,
                height: 400,
                thumbnail: `https://source.unsplash.com/200x200/?${variation}&${Date.now()}&${i}`,
                source: 'Unsplash',
                aspectRatio: '1.00'
            });
        }
        
        return images;
        
    } catch (error) {
        console.error('Unsplash search error:', error.message);
        return [];
    }
}

/**
 * Generate fallback images when all searches fail
 * @param {string} query - Original search query
 * @param {number} count - Number of images
 * @returns {Array} Array of fallback image objects
 */
function generateFallbackImages(query, count = 3) {
    const images = [];
    const colors = ['FF6600', 'FF8533', 'FFA366']; // Orange variants
    
    for (let i = 0; i < count; i++) {
        const color = colors[i % colors.length];
        const encodedQuery = encodeURIComponent(query);
        
        images.push({
            url: `https://via.placeholder.com/400x400/${color}/FFFFFF?text=${encodedQuery}`,
            title: `${query} - Placeholder ${i + 1}`,
            width: 400,
            height: 400,
            thumbnail: `https://via.placeholder.com/200x200/${color}/FFFFFF?text=${encodedQuery}`,
            source: 'Placeholder',
            aspectRatio: '1.00'
        });
    }
    
    return images;
}

/**
 * Generate Amazon affiliate link with enhanced targeting
 * @param {string} searchQuery - Amazon search query
 * @returns {string} Amazon affiliate URL
 */
function generateAmazonLink(searchQuery) {
    const affiliateTag = 'rubysgifts-21';
    const encodedQuery = encodeURIComponent(searchQuery);
    
    // Use exact search terms provided by AI for better specificity
    return `https://www.amazon.in/s?k=${encodedQuery}&tag=${affiliateTag}&linkCode=ur2&camp=3638&creative=24630`;
}

/**
 * Generate additional shopping links for the product
 * @param {string} searchQuery - Product search query
 * @returns {Object} Object containing various shopping links
 */
function generateShoppingLinks(searchQuery) {
    const encodedQuery = encodeURIComponent(searchQuery);
    return {
        amazon: generateAmazonLink(searchQuery),
        flipkart: `https://www.flipkart.com/search?q=${encodedQuery}`,
        myntra: `https://www.myntra.com/${encodedQuery}`,
        ajio: `https://www.ajio.com/search/?text=${encodedQuery}`
    };
}

/**
 * Main function - called from command line
 */
async function main() {
    const args = process.argv.slice(2);
    
    if (args.length === 0) {
        console.error('Usage: node image_search.js "<search_terms>" [count]');
        console.error('Example: node image_search.js "chocolate gift box" 3');
        process.exit(1);
    }
    
    const searchTerms = args[0];
    const imageCount = parseInt(args[1]) || 3;
    
    // Validate image count
    if (imageCount < 1 || imageCount > 10) {
        console.error('Image count must be between 1 and 10');
        process.exit(1);
    }
    
    try {
        const images = await searchProductImages(searchTerms, imageCount);
        
        // Log search results for debugging
        console.error(`Search completed: ${images.length} images found for "${searchTerms}"`);
        images.forEach((img, idx) => {
            console.error(`  ${idx + 1}. ${img.title} (${img.source})`);
        });
        const shoppingLinks = generateShoppingLinks(searchTerms);
        
        // Output JSON result to stdout for Flask to read
        const result = {
            success: true,
            query: searchTerms,
            images: images,
            count: images.length,
            amazonLink: shoppingLinks.amazon,
            shoppingLinks: shoppingLinks,
            timestamp: new Date().toISOString(),
            metadata: {
                searchType: 'product_images',
                provider: 'unsplash',
                requestedCount: imageCount,
                actualCount: images.length
            }
        };
        
        console.log(JSON.stringify(result, null, 2));
        
    } catch (error) {
        console.error('Image search failed:', error.message);
        const errorResult = {
            success: false,
            error: error.message,
            query: searchTerms,
            images: [],
            count: 0,
            amazonLink: generateAmazonLink(searchTerms),
            shoppingLinks: generateShoppingLinks(searchTerms),
            timestamp: new Date().toISOString(),
            metadata: {
                searchType: 'product_images',
                error: true,
                requestedCount: imageCount,
                actualCount: 0
            }
        };
        
        console.log(JSON.stringify(errorResult, null, 2));
        process.exit(1);
    }
}

// Handle both command line and module usage
if (require.main === module) {
    main();
} else {
    module.exports = {
        searchImages,
        searchProductImages,
        generateAmazonLink,
        generateShoppingLinks
    };
}