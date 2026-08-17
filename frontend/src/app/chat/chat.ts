//ng build --configuration production --output-path ../wwwroot
//drag and drop the browser folder in netlify

import { Component, ElementRef, ViewChild, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClientModule } from '@angular/common/http';
import { ChatService, ChatMessage } from '../chat.service';
import { DomSanitizer, SafeUrl } from '@angular/platform-browser';


@Component({
  selector: 'app-chat',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './chat.html',
  styleUrls: ['./chat.css']
})
export class ChatComponent {
botImageUrl: SafeUrl;

  constructor(private sanitizer: DomSanitizer) {
    this.botImageUrl = this.sanitizer.bypassSecurityTrustUrl(
      'https://res.cloudinary.com/dvr9t29vj/image/upload/v1756298027/arin-bot_1_o6lndq.webp'
    );
  }

  public chatService = inject(ChatService);

  messages: ChatMessage[] = this.chatService.getMessages();
  userInput: string = '';

  @ViewChild('messagesWrapper') private messagesWrapper!: ElementRef<HTMLDivElement>;

  sendMessage() {
    if (!this.userInput.trim()) return;
    this.chatService.sendMessage(this.userInput);
    this.userInput = '';
  }

  sendMessageFromButton(btn: { label: string; value: string }) {
    this.chatService.sendMessage(btn.value);
  }

  private scrollToBottom(): void {
    try {
      this.messagesWrapper.nativeElement.scrollTop = this.messagesWrapper.nativeElement.scrollHeight;
    } catch {}
  }

  ngAfterViewChecked() {
    this.scrollToBottom();
  }
}

/* //ng build --configuration production --output-path ../wwwroot


import { Component, ElementRef, inject, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient, HttpClientModule } from '@angular/common/http';

interface ChatMessage {
  text: string;
  from: 'user' | 'bot';
  buttons?: string[];
}

@Component({
  selector: 'app-chat',
  standalone: true,
  imports: [CommonModule, FormsModule, HttpClientModule],
  templateUrl: './chat.html',
  styleUrls: ['./chat.css']
})
export class Chat {
  messages: ChatMessage[] = [];
  userInput: string = '';
  apiUrl = window.location.hostname === 'localhost'
  ? 'http://localhost:3000/chat'   // for dev
  : 'https://arin-bot.onrender.com/chat'; // for Render/live site

  @ViewChild('messagesWrapper') private messagesWrapper!: ElementRef<HTMLDivElement>;
  private http = inject(HttpClient);

  greetingText = "Hello! You are speaking with Arin Leviti's AI assistant. Arin is a freelance web developer with international experience who helps clients reduce production costs and streamline projects without relying on expensive agencies. Feel free to ask about his services, portfolio, or how he can help your business succeed!";
  greetingButtons = ["Learn About Services", "View Portfolio", "Contact Arin"];

  constructor() {
    this.messages.push({ text: this.greetingText, from: 'bot', buttons: this.greetingButtons });
  }

  // Converts URLs in text to clickable links
  linkify(text: string): string {
    const urlPattern = /(\bhttps?:\/\/[^\s]+)/gi;
    return text.replace(urlPattern, '<a href="$1" target="_blank">$1</a>');
  }

  sendMessageFromButton(buttonText: string) {
    this.userInput = buttonText;
    this.sendMessage();
  }

  sendMessage() {
  if (!this.userInput.trim()) return;

  // Add user message
  this.messages.push({ text: this.userInput, from: 'user' });
  const messageToSend = this.userInput;
  this.userInput = '';

  // Expect an array of bot messages from the backend
  this.http.post<{ text: string; buttons: string[] }[]>(this.apiUrl, { message: messageToSend })
    .subscribe({
      next: (responses) => {
        // If backend returns a single object instead of an array, wrap it
        const botMessages = Array.isArray(responses) ? responses : [responses];

        botMessages.forEach(r => {
          this.messages.push({
            text: this.linkify(r.text),
            from: 'bot',
            buttons: r.buttons.length > 0 ? r.buttons : undefined
          });
        });
      },
      error: (err) => {
        console.error('API Error:', err);
        this.messages.push({ text: 'Error contacting server.', from: 'bot' });
      }
    });
}

  private scrollToBottom(): void {
    try {
      this.messagesWrapper.nativeElement.scrollTop = this.messagesWrapper.nativeElement.scrollHeight;
    } catch (err) {}
  }

  ngAfterViewChecked() {
    this.scrollToBottom();
  }
}
 */