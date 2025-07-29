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
            <div class="gift-card" data-gift-index="${index}" style="flex: 0 0 300px; height: calc(100vh - 140px); max-height: 600px; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08); border: 1px solid rgba(255, 102, 0, 0.1); display: flex; flex-direction: column; position: relative; cursor: pointer;" onclick="giftRevealSystem.revealGift(${index})">
                <!-- Gift Box (clickable overlay) -->
                <div class="gift-box" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; background: white; display: flex; flex-direction: column; align-items: center; justify-content: center; z-index: 10; transition: all 0.6s cubic-bezier(0.4, 0, 0.2, 1);">
                    <img class="gift-box-img" src="giftbox-image.png" alt="Gift Box" style="width: 120px; height: 120px; object-fit: contain; margin-bottom: 16px; filter: drop-shadow(0 4px 12px rgba(255, 102, 0, 0.3)); transition: all 0.6s ease;">
                    <p style="color: #ff6600; font-family: 'Playfair Display', serif; font-size: 18px; font-weight: 500; text-transform: lowercase; text-align: center; margin: 0;">
                        <i class="ph ph-gift" style="margin-right: 8px;"></i>
                        click to reveal gift ${index + 1}
                    </p>
                    <div style="width: 40px; height: 3px; background: linear-gradient(135deg, #ff6600, #ff8533); border-radius: 2px; margin-top: 8px; animation: pulse 2s infinite;"></div>
                </div>
                
                <!-- Gift Content (hidden initially) -->
                <div class="gift-content" style="opacity: 0; transform: scale(0.8); transition: all 0.6s cubic-bezier(0.4, 0, 0.2, 1); height: 100%; display: flex; flex-direction: column;">
                    <div style="width: 100%; height: 180px; background: #f0f0f0; display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                        <img src="${this.getGiftImageUrl(gift)}" 
                             alt="${gift.title}" 
                             style="width: 100%; height: 100%; object-fit: cover;"
                             onerror="giftRevealSystem.handleImageError(this)"
                             onload="this.classList.add('loaded')">
                    </div>
                    <div style="padding: 8px; display: flex; flex-direction: column; flex-grow: 1; min-height: 0;">
                        <h3 style="color: #ff6600; font-size: 16px; font-family: 'Playfair Display', serif; font-weight: 600; line-height: 1.2; margin: 0 0 8px 0; display: flex; align-items: center; gap: 6px; flex-shrink: 0;">
                            <i class="ph ph-gift" style="color: #ff6600; font-size: 16px;"></i>
                            ${gift.title}
                        </h3>
                        
                        <!-- Scrollable content sections -->
                        <div style="flex-grow: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 8px; min-height: 0; padding-right: 4px;">
                            <div style="color: #4a5568; font-size: 12px; font-family: 'Plus Jakarta Sans', sans-serif; font-weight: 400; line-height: 1.4;">
                                <div style="display: flex; align-items: flex-start; gap: 6px;">
                                    <i class="ph ph-info" style="color: #666; font-size: 12px; margin-top: 2px; flex-shrink: 0;"></i>
                                    <div><strong style="color: #333;">Why this gift:</strong><br/>${gift.description}</div>
                                </div>
                            </div>
                            ${gift.reaction ? `<div style="color: #4a5568; font-size: 12px; font-family: 'Plus Jakarta Sans', sans-serif; font-weight: 400; line-height: 1.4;">
                                <div style="display: flex; align-items: flex-start; gap: 6px;">
                                    <i class="ph ph-smiley" style="color: #ff6600; font-size: 12px; margin-top: 2px; flex-shrink: 0;"></i>
                                    <div><strong style="color: #333;">Expected reaction:</strong><br/>${gift.reaction}</div>
                                </div>
                            </div>` : ''}
                            ${gift.starter ? `<div style="color: #4a5568; font-size: 12px; font-family: 'Plus Jakarta Sans', sans-serif; font-weight: 400; line-height: 1.4;">
                                <div style="display: flex; align-items: flex-start; gap: 6px;">
                                    <i class="ph ph-hand-heart" style="color: #ff6600; font-size: 12px; margin-top: 2px; flex-shrink: 0;"></i>
                                    <div><strong style="color: #333;">How to present:</strong><br/>${gift.starter}</div>
                                </div>
                            </div>` : ''}
                        </div>
                        
                        <!-- Fixed CTA at bottom -->
                        <div style="margin-top: 8px; padding-top: 8px; flex-shrink: 0;">
                            <a href="${gift.amazon_link || `https://www.amazon.in/s?k=${encodeURIComponent(gift.amazon_search_query || gift.title)}`}" 
                               target="_blank" 
                               rel="noopener noreferrer" 
                               style="width: 100%; height: 36px; background: linear-gradient(135deg, #ff6600, #ff8533); border-radius: 18px; border: none; cursor: pointer; display: flex; align-items: center; justify-content: center; text-decoration: none; transition: all 0.3s ease; gap: 6px;"
                               onclick="event.stopPropagation();">
                                <i class="ph ph-shopping-cart" style="color: white; font-size: 14px;"></i>
                                <span style="color: white; font-size: 13px; font-family: 'Plus Jakarta Sans', sans-serif; font-weight: 500;">Get products</span>
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        `).join('');

        giftCardsContainer.innerHTML = giftBoxesHTML;
        
        // Add CSS for animations
        this.addGiftBoxStyles();
    }

    updateRevealAllButton() {
        const revealAllBtn = document.getElementById('reveal-all-btn');
        if (!revealAllBtn) return;

        const hasUnrevealedGifts = this.revealedGifts.size < this.giftData.length;
        revealAllBtn.style.display = hasUnrevealedGifts ? 'inline-flex' : 'none';
    }

    addGiftBoxStyles() {
        if (document.getElementById('gift-box-styles')) return;
        
        const styles = document.createElement('style');
        styles.id = 'gift-box-styles';
        styles.textContent = `
            @keyframes pulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.5; }
            }
            
            .gift-box.revealing {
                transform: scale(1.05) rotateY(180deg);
                opacity: 0;
            }
            
            .gift-box.revealed {
                display: none !important;
            }
            
            .gift-content.visible {
                opacity: 1 !important;
                transform: scale(1) !important;
            }
            
            .gift-card:hover .gift-box-img {
                transform: scale(1.1) rotate(5deg);
            }
            
            /* Scrollbar styling for content sections */
            .gift-card div[style*="overflow-y: auto"]::-webkit-scrollbar {
                width: 4px;
            }
            
            .gift-card div[style*="overflow-y: auto"]::-webkit-scrollbar-track {
                background: #f1f1f1;
                border-radius: 2px;
            }
            
            .gift-card div[style*="overflow-y: auto"]::-webkit-scrollbar-thumb {
                background: #ff6600;
                border-radius: 2px;
            }
            
            .gift-card div[style*="overflow-y: auto"]::-webkit-scrollbar-thumb:hover {
                background: #e55a00;
            }
        `;
        document.head.appendChild(styles);
    }
    
    revealGift(index) {
        if (this.revealedGifts.has(index)) return;

        this.revealedGifts.add(index);
        
        const giftBox = document.querySelector(`[data-gift-index="${index}"] .gift-box`);
        const giftContent = document.querySelector(`[data-gift-index="${index}"] .gift-content`);

        if (!giftBox || !giftContent) return;

        // Add reveal animation class
        giftBox.classList.add('revealing');

        // Trigger confetti animation
        this.triggerConfetti(giftBox);

        // Animate the reveal
        setTimeout(() => {
            giftBox.classList.add('revealed');
            giftContent.classList.add('visible');
        }, 600);

        // Update reveal all button
        this.updateRevealAllButton();

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