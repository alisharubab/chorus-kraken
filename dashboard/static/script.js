const POLL_INTERVAL = 4000;

function updateContracts(contracts) {
    document.getElementById('c-identity').textContent = contracts.identity || '--';
    document.getElementById('c-reputation').textContent = contracts.reputation || '--';
    document.getElementById('c-validation').textContent = contracts.validation || '--';
}

function updateChainStatus(chain) {
    const statusEl = document.getElementById('chain-status');
    statusEl.textContent = chain?.message || 'Contracts deployed on Base Sepolia — verify at sepolia.basescan.org';
}

function updateMetaDecision(state) {
    const decision = state.decision || {};
    const dec = decision.decision || 'HOLD';

    const el = document.getElementById('meta-decision');
    el.textContent = dec;
    el.className = `decision-pill bg-${dec} ${dec}`;

    document.getElementById('meta-reason').textContent = decision.reason || 'No reason available';
    document.getElementById('market-pair').textContent = state.pair || 'XBTUSD';
    document.getElementById('cycle-time').textContent = state.cycle_timestamp || '--';
}

function updateAgents(state) {
    const grid = document.getElementById('agents-grid');
    grid.innerHTML = '';

    const template = document.getElementById('agent-template');
    const votes = state.current_votes || [];

    if (!votes.length) {
        grid.innerHTML = '<div class="card">No agent votes available yet.</div>';
        return;
    }

    votes.forEach(vote => {
        if (vote.error) {
            const card = document.createElement('div');
            card.className = 'card agent-card';
            card.innerHTML = `<h3>Agent Error</h3><p class="agent-reason">${vote.error}</p>`;
            grid.appendChild(card);
            return;
        }

        const clone = template.content.cloneNode(true);

        const formattedName = (vote.agent_name || 'UnknownAgent').replace(/([a-z])([A-Z])/g, '$1 $2');
        clone.querySelector('.agent-name').textContent = formattedName;
        clone.querySelector('.agent-id').textContent = `ID: ${vote.agent_id ?? '--'}`;

        const direction = vote.direction || 'HOLD';
        const confidence = Number(vote.confidence ?? 0);

        const dirEl = clone.querySelector('.vote-direction');
        dirEl.textContent = direction;
        dirEl.className = `vote-direction ${direction}`;

        clone.querySelector('.confidence span').textContent = `${confidence}%`;
        const fill = clone.querySelector('.fill');
        setTimeout(() => {
            fill.style.width = `${Math.max(0, Math.min(100, confidence))}%`;
            fill.className = `fill fill-${direction}`;
        }, 50);

        clone.querySelector('.agent-reason').textContent = vote.reason || 'No reasoning available.';
        clone.querySelector('.rep-value').textContent = vote.reputation ?? 50;

        grid.appendChild(clone);
    });
}

function updateArtifacts(state) {
    const list = document.getElementById('artifact-list');
    const items = state.recent_artifacts || [];
    list.innerHTML = '';

    if (!items.length) {
        list.innerHTML = '<li class="artifact-item">No artifacts yet.</li>';
        return;
    }

    items.slice(0, 8).forEach(item => {
        const li = document.createElement('li');
        li.className = 'artifact-item';
        const ts = item.timestamp ? new Date(item.timestamp * 1000).toLocaleString() : '--';
        li.textContent = `${item.artifact_type} | ${item.file} | ${ts}`;
        list.appendChild(li);
    });
}

function updateLastTrade(state) {
    const t = state.last_trade_decision;
    document.getElementById('trade-type').textContent = t?.artifact_type || 'No trade artifact yet';
    document.getElementById('trade-file').textContent = t?.file || '--';
    document.getElementById('trade-time').textContent = t?.timestamp ? new Date(t.timestamp * 1000).toLocaleString() : '--';
}

function pollState() {
    fetch('/api/state')
        .then(res => res.json())
        .then(state => {
            if (state.error) {
                console.error('Error fetching state:', state.error);
                return;
            }
            updateContracts(state.contracts || {});
            updateChainStatus(state.chain_status);
            updateMetaDecision(state);
            updateAgents(state);
            updateArtifacts(state);
            updateLastTrade(state);
        })
        .catch(err => console.error('Error fetching state:', err));
}

pollState();
setInterval(pollState, POLL_INTERVAL);
