const canvas = document.getElementById('canvas');
const ctx = canvas.getContext('2d');
const stats = document.getElementById('stats');

let width, height;
let particles = [];
let mouse = { x: -1000, y: -1000, active: false };

// UI Controls
const particleCountInput = document.getElementById('particleCount');
const forceFieldInput = document.getElementById('forceField');
const speedInput = document.getElementById('speed');

function resize() {
    width = canvas.width = window.innerWidth;
    height = canvas.height = window.innerHeight;
    initParticles();
}

class Particle {
    constructor() {
        this.reset();
    }

    reset() {
        this.x = Math.random() * width;
        this.y = Math.random() * height;
        this.vx = (Math.random() - 0.5) * 2;
        this.vy = (Math.random() - 0.5) * 2;
        this.radius = Math.random() * 2 + 1;
        this.color = Math.random() > 0.5 ? '#00f3ff' : '#ff00e5';
        this.alpha = Math.random() * 0.5 + 0.2;
    }

    update() {
        // Basic movement
        this.x += this.vx * (speedInput.value / 3);
        this.y += this.vy * (speedInput.value / 3);

        // Mouse interaction
        const dx = mouse.x - this.x;
        const dy = mouse.y - this.y;
        const distance = Math.sqrt(dx * dx + dy * dy);
        
        if (distance < 250) {
            const force = (250 - distance) / 250;
            const attraction = forceFieldInput.value / 100;
            
            this.vx += dx * force * attraction;
            this.vy += dy * force * attraction;
            
            // Limit speed
            const speed = Math.sqrt(this.vx * this.vx + this.vy * this.vy);
            if (speed > 5) {
                this.vx *= 0.95;
                this.vy *= 0.95;
            }
        }

        // Friction
        this.vx *= 0.98;
        this.vy *= 0.98;

        // Wrap around
        if (this.x < 0) this.x = width;
        if (this.x > width) this.x = 0;
        if (this.y < 0) this.y = height;
        if (this.y > height) this.y = 0;
    }

    draw() {
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
        ctx.fillStyle = this.color;
        ctx.globalAlpha = this.alpha;
        ctx.shadowBlur = 10;
        ctx.shadowColor = this.color;
        ctx.fill();
        ctx.globalAlpha = 1;
        ctx.shadowBlur = 0;
    }
}

function initParticles() {
    particles = [];
    const count = parseInt(particleCountInput.value);
    for (let i = 0; i < count; i++) {
        particles.push(new Particle());
    }
}

function animate() {
    ctx.clearRect(0, 0, width, height);
    
    // Draw connections (slightly expensive but looks premium)
    ctx.lineWidth = 0.5;
    for (let i = 0; i < particles.length; i++) {
        particles[i].update();
        particles[i].draw();

        // Check for connections
        for (let j = i + 1; j < particles.length; j++) {
            const dx = particles[i].x - particles[j].x;
            const dy = particles[i].y - particles[j].y;
            const dist = Math.sqrt(dx * dx + dy * dy);
            
            if (dist < 100) {
                ctx.beginPath();
                ctx.moveTo(particles[i].x, particles[i].y);
                ctx.lineTo(particles[j].x, particles[j].y);
                ctx.strokeStyle = `rgba(0, 243, 255, ${0.2 * (1 - dist/100)})`;
                ctx.stroke();
            }
        }
    }

    // Update stats
    if (Math.random() > 0.95) {
        stats.innerHTML = `
            SYSTEM_STATUS: ACTIVE<br>
            PARTICLE_COUNT: ${particles.length}<br>
            CORE_LOAD: ${Math.floor(Math.random() * 20 + 30)}%<br>
            LATENCY: ${Math.floor(Math.random() * 5 + 2)}ms
        `;
    }

    requestAnimationFrame(animate);
}

window.addEventListener('resize', resize);
window.addEventListener('mousemove', (e) => {
    mouse.x = e.clientX;
    mouse.y = e.clientY;
});

window.addEventListener('mousedown', () => {
    particles.forEach(p => {
        const dx = mouse.x - p.x;
        const dy = mouse.y - p.y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < 300) {
            p.vx -= dx / 10;
            p.vy -= dy / 10;
        }
    });
});

particleCountInput.addEventListener('input', initParticles);

resize();
animate();
