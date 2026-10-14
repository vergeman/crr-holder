import { useRef, useState } from "react";

// The ref saves the starting width and pointer X for each drag. Pointer movement
// updates width state, which updates --portfolio-width in the aside's CSS style.
// The ref and resize handlers ultimately control the pane's CSS width.
const boundPortfolioPanelWidth = (width) =>
  Math.max(320, Math.min(window.innerWidth - 500, width));

export default function PortfolioPanel({ children }) {
  const [portfolioWidth, setPortfolioWidth] = useState(680);
  const resizeStart = useRef(null);

  // Pointer capture keeps the drag active outside the divider.
  function startResize(event) {
    if (event.button !== 0) return;
    resizeStart.current = { x: event.clientX, width: portfolioWidth };
    event.currentTarget.setPointerCapture(event.pointerId);
    event.preventDefault();
  }

  function moveResize(event) {
    if (!resizeStart.current) return;
    setPortfolioWidth(
      boundPortfolioPanelWidth(
        resizeStart.current.width + event.clientX - resizeStart.current.x
      )
    );
  }

  function finishResize(event) {
    resizeStart.current = null;
    event.currentTarget.releasePointerCapture(event.pointerId);
  }

  // Cancellation or lost capture also ends the drag.
  function cancelResize() {
    resizeStart.current = null;
  }

  function keyboardResize(event) {
    if (event.key !== "ArrowLeft" && event.key !== "ArrowRight") return;
    event.preventDefault();
    setPortfolioWidth((width) =>
      boundPortfolioPanelWidth(width + (event.key === "ArrowRight" ? 20 : -20))
    );
  }

  return (
    <>
      <aside style={{ "--portfolio-width": `${portfolioWidth}px` }}>
        {children}
      </aside>

      {/* Dragging this divider changes the portfolio pane width. */}
      <div
        className="portfolio-resize"
        role="separator"
        tabIndex={0}
        aria-label="Resize portfolio pane"
        aria-orientation="vertical"
        aria-valuemin={320}
        aria-valuemax={Math.max(320, window.innerWidth - 500)}
        aria-valuenow={portfolioWidth}
        onPointerDown={startResize}
        onPointerMove={moveResize}
        onPointerUp={finishResize}
        onPointerCancel={cancelResize}
        onLostPointerCapture={cancelResize}
        onKeyDown={keyboardResize}
      />
    </>
  );
}
