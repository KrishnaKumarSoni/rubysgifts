// Gift Box Reveal System with Confetti Animation
class GiftRevealSystem {
    constructor() {
        this.revealedGifts = new Set();
        this.giftData = [];
        this.init();
    }

    init() {
        // Load confetti library dynamically
        this.loadConfettiLibrary();
    }

    loadConfettiLibrary() {
        if (window.confetti) return;
        
        const script = document.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/npm/canvas-confetti@1.6.0/dist/confetti.browser.min.js';
        script.onload = () => {
            console.log('Confetti library loaded');
        };
        document.head.appendChild(script);
    }

    setGiftData(gifts) {
        this.giftData = gifts;
        this.revealedGifts.clear();
        // No need to preload images separately since backend provides them
        console.log('Gift data set:', gifts);
    }

    getGiftImageUrl(gift) {
        // Use backend-provided images if available
        if (gift.images && gift.images.length > 0) {
            return gift.images[0].url;
        }
        
        // Fallback to search terms-based image
        if (gift.image_search_terms) {
            const cleanTerms = gift.image_search_terms.toLowerCase().replace(/[^a-z0-9\s]/g, '').trim();
            const keywords = cleanTerms.split(' ').slice(0, 2).join(',');
            return `https://source.unsplash.com/300x200/?${keywords}&sig=${Date.now()}`;
        }
        
        // Final fallback placeholder
        return `https://via.placeholder.com/300x200/e2e8f0/4a5568?text=${encodeURIComponent(gift.title || 'Gift')}`;
    }

    // Legacy method - no longer needed since backend provides images
    preloadImages() {
        console.log('Image preloading skipped - using backend-provided images');
    }

    handleImageError(imgElement) {
        // Mark the container as having an error
        const container = imgElement.closest('.gift-image-container');
        if (container) {
            container.classList.add('error');
        }
        
        // Hide the broken image
        imgElement.style.display = 'none';
        
        // Log the error for debugging
        console.warn('Gift image failed to load:', imgElement.src);
    }

    renderGiftBoxes() {
        const giftCardsContainer = document.getElementById('gift-cards');
        if (!giftCardsContainer) return;

        const giftBoxesHTML = this.giftData.map((gift, index) => `
            <div class="gift-card" data-gift-index="${index}">
                <div class="gift-image-container">
                    <img src="${this.getGiftImageUrl(gift)}" 
                         alt="${gift.title}" 
                         class="gift-image" 
                         onerror="giftRevealSystem.handleImageError(this)"
                         onload="this.classList.add('loaded')">
                </div>
                <h3 class="gift-title">${gift.title}</h3>
                <p class="gift-description">${gift.description}</p>
                ${gift.starter ? `<div class="gift-starter"><strong>How to present it:</strong> ${gift.starter}</div>` : ''}
                ${gift.reaction ? `<div class="gift-reaction"><strong>Expected reaction:</strong> ${gift.reaction}</div>` : ''}
                <div class="gift-actions">
                    <a href="${gift.amazon_link || `https://www.amazon.in/s?k=${encodeURIComponent(gift.amazon_search_query || gift.title)}`}" 
                       target="_blank" 
                       rel="noopener noreferrer" 
                       class="amazon-btn">
                        <i class="ph-bold ph-shopping-cart"></i>
                        <span>Get products</span>
                    </a>
                </div>
            </div>
        `).join('');

        giftCardsContainer.innerHTML = giftBoxesHTML;
    }

    updateRevealAllButton() {
        const revealAllBtn = document.getElementById('reveal-all-btn');
        if (!revealAllBtn) return;

        const hasUnrevealedGifts = this.revealedGifts.size < this.giftData.length;
        revealAllBtn.style.display = hasUnrevealedGifts ? 'inline-flex' : 'none';
    }

    revealGift(index) {
        if (this.revealedGifts.has(index)) return;

        this.revealedGifts.add(index);
        
        const giftBox = document.querySelector(`[data-gift-index="${index}"] .gift-box`);
        const giftBoxImg = document.querySelector(`[data-gift-index="${index}"] .gift-box-img`);
        const giftContent = document.querySelector(`[data-gift-index="${index}"] .gift-content`);

        if (!giftBox) return;

        // Add reveal animation class
        giftBox.classList.add('revealing');

        // Trigger confetti animation
        this.triggerConfetti(giftBox);

        // Animate the reveal
        setTimeout(() => {
            if (giftBoxImg) giftBoxImg.classList.add('hidden');
            if (giftContent) giftContent.classList.add('visible');
            giftBox.classList.add('revealed');
            giftBox.classList.remove('revealing');
        }, 600);

        // Announce to screen readers
        this.announceGiftReveal(this.giftData[index].title);
    }

    triggerConfetti(element) {
        if (!window.confetti) return;

        const rect = element.getBoundingClientRect();
        const x = (rect.left + rect.width / 2) / window.innerWidth;
        const y = (rect.top + rect.height / 2) / window.innerHeight;

        // Primary confetti burst
        confetti({
            particleCount: 100,
            spread: 70,
            origin: { x, y },
            colors: ['#ff6600', '#ff8533', '#ffaa66', '#ffd700', '#ff69b4']
        });

        // Secondary burst with different timing
        setTimeout(() => {
            confetti({
                particleCount: 50,
                spread: 50,
                origin: { x, y },
                colors: ['#ff6600', '#ff8533', '#ffaa66']
            });
        }, 200);

        // Falling confetti
        setTimeout(() => {
            confetti({
                particleCount: 30,
                spread: 100,
                origin: { x: x - 0.1, y: y - 0.1 },
                colors: ['#ffd700', '#ff69b4', '#00ff00']
            });
        }, 400);
    }

    announceGiftReveal(giftTitle) {
        const announcement = document.createElement('div');
        announcement.setAttribute('aria-live', 'polite');
        announcement.setAttribute('aria-atomic', 'true');
        announcement.className = 'sr-only';
        announcement.textContent = `Gift revealed: ${giftTitle}`;
        
        document.body.appendChild(announcement);
        
        setTimeout(() => {
            document.body.removeChild(announcement);
        }, 1000);
    }

    revealAllGifts() {
        for (let i = 0; i < this.giftData.length; i++) {
            if (!this.revealedGifts.has(i)) {
                setTimeout(() => this.revealGift(i), i * 500);
            }
        }
    }
}

// Global instance
const giftRevealSystem = new GiftRevealSystem();

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = GiftRevealSystem;
} 