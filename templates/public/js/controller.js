'use strict';

const switches = document.querySelectorAll('.switch');
const refreshButton = document.querySelector('#refresh-status');
const connection = document.querySelector('#connection');
const fields = {living: '#toggleswitch0', bedroom: '#toggleswitch1'};
let busy = false;

function show(states) {
    for (const [room, selector] of Object.entries(fields)) {
        document.querySelector(selector).value = states[room] === null
            ? 'unknown' : (states[room] ? 'on' : 'off');
    }
}

function lock(value) {
    busy = value;
    switches.forEach(control => { control.disabled = value; });
    refreshButton.disabled = value;
}

async function request(url, options = {}) {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 10000);
    try {
        const response = await fetch(url, {...options, signal: controller.signal, cache: 'no-store'});
        if (!response.ok) throw new Error('Request failed');
        const result = await response.json();
        const states = result && result.states;
        if (!states || Object.keys(states).length !== 2 ||
            !Object.keys(fields).every(room => states[room] === null || typeof states[room] === 'boolean')) {
            throw new Error('Invalid state response');
        }
        return states;
    } finally {
        clearTimeout(timeout);
    }
}

async function refresh(message) {
    lock(true);
    try {
        show(await request('status'));
        connection.textContent = message || 'Status refreshed.';
    } catch (error) {
        show({living: null, bedroom: null});
        connection.textContent = 'Hardware unavailable. State is unknown; refresh status to reconnect.';
    } finally {
        lock(false);
    }
}

refreshButton.addEventListener('click', () => {
    if (!busy) refresh();
});
document.querySelector('#switches').addEventListener('submit', event => event.preventDefault());
switches.forEach(control => control.addEventListener('change', async () => {
    if (busy) return;
    const body = new URLSearchParams({[control.name]: control.value});
    lock(true);
    try {
        show(await request('index', {method: 'POST', body}));
        connection.textContent = 'Command accepted.';
        lock(false);
    } catch (error) {
        await refresh('Command outcome was uncertain. Showing latest controller state.');
    }
}));
