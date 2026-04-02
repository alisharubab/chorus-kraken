const POLL_INTERVAL = 3000;

function updateContracts(data) {
    if (data.identity) document.getElementById('c-identity').textContent = data.identity;
    if (data.reputation) document.getElementById('c-reputation').textContent = data.reputation;
    if (data.validation) document.getElementById('c-validation').textContent = data.validation;
}

function updateMetaDecision(data) {
    const dec = data.decision.decision || 'HOLD';
    const el = document.getElementById('meta-decision');
    el.textContent = dec;
    el.className = `decision-pill bg-${dec} ${dec}`;
    
    document.getElementById('meta-reason').textContent = data.decision.reason;
    document.getElementById('market-pair').textContent = data.pair;
    document.getElementById('cycle-time').textContent = data.cycle_timestamp;
}

function getReputation(weights, agentName) {
    if (weights && weights[agentName]) {
        return weights[agentName].reputation || 50;
    }
    return 50;
}

function updateAgents(data) {
    const grid = document.getElementById('agents-grid');
    grid.innerHTML = '';
    const template = document.getElementById('agent-template');
    
    const weights = data.decision.vote_breakdown;

    data.votes.forEach(vote => {
        const clone = template.content.cloneNode(true);
        const card = clone.querySelector('.agent-card');
        
        // Insert a space between lowercase and uppercase letters
        const formattedName = vote.agent_name.replace(/([a-z])([A-Z])/g, '$1 $2');
        clone.querySelector('.agent-name').textContent = formattedName;
        clone.querySelector('.agent-id').textContent = `ID: ${vote.agent_id}`;
        
        const dirEl = clone.querySelector('.vote-direction');
        dirEl.textContent = vote.direction;
        dirEl.className = `vote-direction ${vote.direction}`;
        
        clone.querySelector('.confidence span').textContent = `${vote.confidence}%`;
        const fill = clone.querySelector('.fill');
        // Small timeout to allow css transition
        setTimeout(() => {
            fill.style.width = `${vote.confidence}%`;
            fill.className = `fill fill-${vote.direction}`;
        }, 50);
        
        clone.querySelector('.agent-reason').textContent = vote.reason || 'No specific reasoning provided.';
        
        const rep = getReputation(weights, vote.agent_name);
        clone.querySelector('.rep-value').textContent = rep;
        
        grid.appendChild(clone);
    });
}

function pollState() {
    fetch('/api/state')
        .then(res => res.json())
        .then(data => {
            if (!data.error) {
                updateMetaDecision(data);
                updateAgents(data);
            }
        })
        .catch(err => console.error("Error fetching state:", err));
}

function fetchContracts() {
    fetch('/api/contracts')
        .then(res => res.json())
        .then(data => {
            if (!data.error) {
                updateContracts(data);
            }
        })
        .catch(err => console.error("Error fetching contracts:", err));
}

// Initial fetch & set poll
fetchContracts();
pollState();
setInterval(pollState, POLL_INTERVAL);
