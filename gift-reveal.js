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
    }

    renderGiftBoxes() {
        const giftCardsContainer = document.getElementById('gift-cards');
        if (!giftCardsContainer) return;

        const giftBoxesHTML = this.giftData.map((gift, index) => `
            <div class="gift-box-container" data-gift-index="${index}">
                <div class="gift-box ${this.revealedGifts.has(index) ? 'revealed' : ''}" 
                     onclick="giftRevealSystem.revealGift(${index})">
                    <div class="gift-box-image">
                        <img src="https://gallery.yopriceville.com/var/albums/Free-Clipart-Pictures/Valentine%27s-Day-PNG/Transparent_Gift_Box_with_Heart_PNG_Clipart.png?m=1629819649" 
                             alt="Gift Box" 
                             class="gift-box-img ${this.revealedGifts.has(index) ? 'hidden' : ''}">
                    </div>
                    <div class="gift-content ${this.revealedGifts.has(index) ? 'visible' : ''}">
                        <h3 class="gift-title">${gift.title}</h3>
                        <p class="gift-description">${gift.description}</p>
                        ${gift.starter ? `<div class="gift-starter"><strong>How to present it:</strong> ${gift.starter}</div>` : ''}
                        ${gift.reaction ? `<div class="gift-reaction"><strong>Expected reaction:</strong> ${gift.reaction}</div>` : ''}
                    </div>
                </div>
                ${!this.revealedGifts.has(index) ? `
                    <div class="gift-box-prompt">
                        <i class="ph ph-gift"></i>
                        <span>Click to reveal your gift!</span>
                    </div>
                ` : ''}
            </div>
        `).join('');

        giftCardsContainer.innerHTML = giftBoxesHTML;
        this.updateRevealAllButton();
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
        const giftPrompt = document.querySelector(`[data-gift-index="${index}"] .gift-box-prompt`);

        if (!giftBox) return;

        // Add reveal animation class
        giftBox.classList.add('revealing');
        
        // Hide the prompt
        if (giftPrompt) {
            giftPrompt.style.opacity = '0';
            setTimeout(() => giftPrompt.remove(), 300);
        }

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
        
        // Update reveal all button
        this.updateRevealAllButton();
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