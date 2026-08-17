import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';

export interface ChatMessage {
  text: string;
  from: 'user' | 'bot';
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
    : 'https://docs-rag-assistant-backend-224143145108.europe-west3.run.app/chat';

  constructor() {
    this.addMessage({
      text: "Hi — I'm a clinical reference assistant for paracetamol (acetaminophen), grounded in official EU/UK regulatory documentation (SmPCs, a Public Assessment Report, and a drug-interactions reference). Ask me about dosing, contraindications, interactions, or special-population guidance. I'll only answer from the source documents and will tell you when something isn't covered, rather than guessing.",
      from: 'bot'
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
    return this.http.post<{ text: string }>(this.apiUrl, {
      message: userText,
      sessionId: this.sessionId
    })
      .subscribe({
        next: (response) => {
          clearTimeout(this.typingTimeout);
          this.isTyping = false;
          this.isColdStart = false;

          this.addMessage({
            text: this.linkify(response.text),
            from: 'bot'
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