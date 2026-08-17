import { Component, ElementRef, ViewChild, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ChatService, ChatMessage } from '../chat.service';
import { DomSanitizer, SafeHtml, SafeUrl } from '@angular/platform-browser';
import { marked } from 'marked';

@Component({
  selector: 'app-chat',
  standalone: true,
  imports: [FormsModule],
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

  // Bot responses come back as markdown (the LLM formats with **bold**,
  // bullet lists, etc). marked.parse() converts that markdown into an HTML
  // string; bypassSecurityTrustHtml() tells Angular to trust and render it
  // rather than escaping it as plain text. This is safe here because the
  // content originates from our own backend, which only answers from a
  // fixed, controlled set of source documents — not arbitrary user input
  // being reflected back as HTML.
  renderMarkdown(text: string): SafeHtml {
    const html = marked.parse(text, { async: false }) as string;
    return this.sanitizer.bypassSecurityTrustHtml(html);
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