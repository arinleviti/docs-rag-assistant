import { Component, signal } from '@angular/core';
import { Background } from './background/background';

@Component({
  selector: 'app-root',
  imports: [  Background],
  templateUrl: './app.html',
  styleUrl: './app.css'
})
export class App {
  protected readonly title = signal('frontend');
}
