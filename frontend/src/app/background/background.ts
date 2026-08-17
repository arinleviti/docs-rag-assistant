import { Component } from '@angular/core';
import { ChatComponent } from '../chat/chat';

@Component({
  selector: 'app-background',
  imports: [ChatComponent],
  templateUrl: './background.html',
  styleUrl: './background.css'
})
export class Background {}