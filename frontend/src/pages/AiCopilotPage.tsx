import { useEffect, useRef, useState } from "react";
import axios from "axios";
import { API_BASE_URL } from "../config";

type AiRiskSummary = {
  portfolio_id: number;
  summary: string;
};

type ChatMessage = {
  role: "user" | "ai";
  text: string;
};

const SUGGESTED_AI_PROMPTS = [
  "What is the biggest concentration risk?",
  "Which assets contribute the most portfolio risk?",
  "Summarize this portfolio for a risk committee.",
  "What sectors should I monitor most closely?",
  "Is this portfolio sufficiently diversified?",
];

function AiCopilotPage() {
  const selectedPortfolioId = 1;

  const [aiSummary, setAiSummary] = useState<AiRiskSummary | null>(null);
  const [aiLoading, setAiLoading] = useState(false);

  const [aiQuestion, setAiQuestion] = useState("");
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [aiQuestionLoading, setAiQuestionLoading] = useState(false);
  const chatContainerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!chatContainerRef.current) return;

    chatContainerRef.current.scrollTop =
        chatContainerRef.current.scrollHeight;
    }, [chatMessages]);

  function generateAiRiskSummary() {
    setAiLoading(true);
    setAiSummary(null);

    axios
      .post(`${API_BASE_URL}/api/portfolio/${selectedPortfolioId}/ai-risk-summary`)
      .then((res) => {
        setAiSummary(res.data);
      })
      .finally(() => {
        setAiLoading(false);
      });
  }

  function askAiRiskAnalyst() {
    const question = aiQuestion.trim();

    if (!question) return;

    setChatMessages((prev) => [
      ...prev,
      {
        role: "user",
        text: question,
      },
    ]);

    setAiQuestion("");
    setAiQuestionLoading(true);

    axios
      .post(`${API_BASE_URL}/api/portfolio/${selectedPortfolioId}/ask-ai`, {
        question,
        chat_history: chatMessages,
      })
      .then((res) => {
        setChatMessages((prev) => [
          ...prev,
          {
            role: "ai",
            text: res.data.answer,
          },
        ]);
      })
      .finally(() => {
        setAiQuestionLoading(false);
      });
  }

  return (
    <>
      <section className="table-card">
        <div className="chart-header">
          <div>
            <p className="eyebrow">AI Analyst</p>
            <h2>AI Risk Summary</h2>
          </div>
        </div>

        <p className="subtitle">
          Generate a natural-language portfolio risk summary using calculated
          risk metrics, sector exposure, holdings, and risk contribution data.
        </p>

        <button
          className="primary-button"
          onClick={generateAiRiskSummary}
          disabled={aiLoading}
        >
          {aiLoading ? "Generating Summary..." : "Generate AI Risk Summary"}
        </button>

        {aiSummary && (
          <div className="ai-summary-box">
            <pre>{aiSummary.summary}</pre>
          </div>
        )}
      </section>

      <section className="table-card">
        <div className="chart-header">
          <div>
            <p className="eyebrow">AI Copilot</p>
            <h2>Ask AI Risk Analyst</h2>
          </div>
        </div>

        <p className="subtitle">
          Ask natural-language questions about this portfolio’s risk,
          concentration, sector exposure, or risk drivers.
        </p>

        <div className="suggested-prompts">
          {SUGGESTED_AI_PROMPTS.map((prompt) => (
            <button
              key={prompt}
              onClick={() => setAiQuestion(prompt)}
              type="button"
            >
              {prompt}
            </button>
          ))}
        </div>

        <div className="ai-question-row">
          <input
            type="text"
            value={aiQuestion}
            onChange={(e) => setAiQuestion(e.target.value)}
            placeholder="e.g. What is the biggest concentration risk?"
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                askAiRiskAnalyst();
              }
            }}
          />

          <button
            className="primary-button"
            onClick={askAiRiskAnalyst}
            disabled={aiQuestionLoading}
          >
            {aiQuestionLoading ? "Thinking..." : "Ask"}
          </button>
        </div>

        <div 
            className="chat-box"
            ref={chatContainerRef}
        >
          {chatMessages.length === 0 && (
            <p className="chat-empty">
              Try asking: “What is the biggest concentration risk?”
            </p>
          )}

          {chatMessages.map((message, index) => (
            <div
              key={index}
              className={`chat-message ${
                message.role === "user" ? "user-message" : "ai-message"
              }`}
            >
              <p className="chat-role">
                {message.role === "user" ? "You" : "AI Risk Analyst"}
              </p>
              <pre>{message.text}</pre>
            </div>
          ))}

          {aiQuestionLoading && (
            <div className="chat-message ai-message">
              <p className="chat-role">AI Risk Analyst</p>
              <pre>Thinking...</pre>
            </div>
          )}

          
        </div>
      </section>
    </>
  );
}

export default AiCopilotPage;
