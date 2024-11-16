document.getElementById('send_message').addEventListener('click', async () => {
    const userInput = document.getElementById('user_input').value;
    const chatbox = document.getElementById('chatbox');
    const instructions = "{{ instructions }}";

    const response = await fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userInput, instructions }),
    });

    const data = await response.json();
    if (data.response) {
        chatbox.value += `You: ${userInput}\n`;
        chatbox.value += `Bot: ${data.response}\n`;
    }
});
