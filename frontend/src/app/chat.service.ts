import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';

export interface ChatMessage {
  text: string;
  from: 'user' | 'bot';
  buttons?: { label: string; value: string }[];
}

@Injectable({
  providedIn: 'root'
})
export class ChatService {
  private http = inject(HttpClient);

  private messages: ChatMessage[] = [];
   isTyping = false;
   isColdStart = false;
  private typingTimeout?: ReturnType<typeof setTimeout>;
   

  // Generate a random sessionId once when the service is created.
  // This persists for the lifetime of the browser tab — same idea as
  // a UUID stored in memory, not in localStorage, so it resets on page refresh.
  private sessionId: string = crypto.randomUUID();

  // pick API URL depending on env
  private apiUrl = window.location.hostname === 'localhost'
    ? 'http://localhost:8000/chat'
    : 'https://arin-bot-py-224143145108.europe-west3.run.app/chat';

  constructor() {
  this.addMessage({
    text: "Hi! I'm Arin's AI assistant — ask me anything about his skills, projects, or experience. I'm also a live demo of what Arin can build: a full RAG pipeline in Python, deployed on Google Cloud Run.",
    from: 'bot',
    buttons: [
      { label: "How was this chatbot built?", value: "How was this chatbot built?" },
      { label: "Tell me about his AI work", value: "Tell me about his AI work" },
      { label: "Is he available for hire?", value: "Is he available for hire?" }
    ]
  });
}

  getMessages(): ChatMessage[] {
    return this.messages;
  }

  addMessage(message: ChatMessage): void {
    this.messages.push(message);
  }

  clearMessages(): void {
    this.messages = [];
  }

  // converts URLs to clickable links
  private linkify(text: string): string {
    const urlPattern = /(\bhttps?:\/\/[^\s]+)/gi;
    return text.replace(urlPattern, '<a href="$1" target="_blank">$1</a>');
  }

  sendMessage(userText: string) {
    // add user message locally
    this.addMessage({ text: userText, from: 'user' });
    this.isTyping = true;
    this.isColdStart = false;

    this.typingTimeout = setTimeout(() => {
    this.isColdStart = true;
  }, 5000);

    // Include sessionId alongside message so the backend can track
    // conversation history per browser session
    return this.http.post<{ text: string; buttons?: string[] }[]>(this.apiUrl, { 
      message: userText,
      sessionId: this.sessionId
    })
      .subscribe({
        next: (responses) => {
          clearTimeout(this.typingTimeout);
          this.isTyping = false;
          this.isColdStart = false;
          const botMessages = Array.isArray(responses) ? responses : [responses];

          botMessages.forEach(r => {
            this.addMessage({
              text: this.linkify(r.text),
              from: 'bot',
              buttons: r.buttons?.map(b => ({ label: b, value: b }))
            });
          });
        },
        error: (err) => {
           clearTimeout(this.typingTimeout);
          console.error('API Error:', err);
          this.isTyping = false;
          this.isColdStart = false;
          this.addMessage({ text: 'Error contacting server.', from: 'bot' });
        }
      });
  }
}
