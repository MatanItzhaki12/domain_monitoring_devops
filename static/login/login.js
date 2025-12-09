document.addEventListener('DOMContentLoaded', function () {
    const form = document.querySelector('form#login-form');
    const username = document.querySelector('#username');
    const password = document.querySelector('#password');
    const failedLoginMessage = document.getElementById('failed-login');
    const box = document.querySelector('#login-container');
    const title = document.querySelector('.title');

    title.addEventListener('click', function() {
        window.location.href = '/';
    });

    form.addEventListener('submit', function(event) {
        event.preventDefault();
        sendLogin(username.value, password.value);
    });

    function triggerShake(element) {
    element.classList.add('shake');
    setTimeout(() => element.classList.remove('shake'), 400);
    }


    async function sendLogin(username, password) {
        const message = { "username": username, "password": password };
        const response = await fetch('/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(message)
        });
        if (response.ok) {
            window.location.href = '/dashboard';
        } else {
            const data = await response.json();
            failedLoginMessage.textContent = data.error || 'Login failed';
            failedLoginMessage.style.display = 'block';
            triggerShake(box);
        }
    }

    // Optionally, handle register button click
    document.getElementById('register').addEventListener('click', function() {
        window.location.href = '/register';
    });
});
