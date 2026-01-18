// Federal Regulatory Comment Bot - Client-side filtering

document.addEventListener('DOMContentLoaded', function() {
    // Get elements
    const filterButtons = document.querySelectorAll('.filter-btn');
    const periodCards = document.querySelectorAll('.period-card');
    const periodsContainer = document.getElementById('periodsContainer');
    
    // Track active filter
    let activeFilter = 'all';
    
    // Add click handlers to filter buttons
    filterButtons.forEach(button => {
        button.addEventListener('click', function() {
            const topic = this.getAttribute('data-topic');
            
            // Update active filter
            activeFilter = topic;
            
            // Update button states
            filterButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');
            
            // Filter cards
            filterPeriods(topic);
        });
    });
    
    /**
     * Filter period cards by topic
     */
    function filterPeriods(topic) {
        let visibleCount = 0;
        
        periodCards.forEach(card => {
            if (topic === 'all') {
                card.classList.remove('hidden');
                visibleCount++;
            } else {
                // Get topics for this card
                const topicsAttr = card.getAttribute('data-topics');
                let cardTopics = [];
                
                try {
                    cardTopics = JSON.parse(topicsAttr) || [];
                } catch (e) {
                    console.error('Error parsing topics:', e);
                }
                
                // Show if matches filter
                if (cardTopics.includes(topic)) {
                    card.classList.remove('hidden');
                    visibleCount++;
                } else {
                    card.classList.add('hidden');
                }
            }
        });
        
        // Show empty state if no results
        updateEmptyState(visibleCount, topic);
    }
    
    /**
     * Show/hide empty state message
     */
    function updateEmptyState(visibleCount, topic) {
        // Remove existing empty state
        const existingEmpty = periodsContainer.querySelector('.empty-state');
        if (existingEmpty) {
            existingEmpty.remove();
        }
        
        // Add empty state if no results
        if (visibleCount === 0) {
            const topicName = topic === 'all' ? 'all topics' : topic.replace(/_/g, ' ');
            const emptyDiv = document.createElement('div');
            emptyDiv.className = 'empty-state';
            emptyDiv.innerHTML = `
                <h3>No comment periods found</h3>
                <p>There are currently no open comment periods for ${topicName}.</p>
                <p>Try selecting a different topic or check back later.</p>
            `;
            periodsContainer.insertBefore(emptyDiv, periodsContainer.firstChild);
        }
    }
    
    /**
     * Initialize on page load
     */
    function init() {
        console.log(`Loaded ${periodCards.length} comment periods`);
        
        // Show all by default
        filterPeriods('all');
    }
    
    init();
});
