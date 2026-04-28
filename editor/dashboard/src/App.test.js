// Mock Monaco Editor because it doesn't run in JSDOM
jest.mock('@monaco-editor/react', () => {
  return function MockEditor(props) {
    return <textarea data-testid="monaco-mock" onChange={(e) => props.onChange(e.target.value)} value={props.value} />;
  };
});
import '@testing-library/jest-dom';
import { render, screen } from '@testing-library/react';
import App from './App';

test('renders the Save Changes button', () => {
  render(<App />);
  const buttonElement = screen.getByText(/Save Changes/i);
  expect(buttonElement).toBeInTheDocument();
});
