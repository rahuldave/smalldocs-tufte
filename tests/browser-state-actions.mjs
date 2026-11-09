/** Pass this function to CUA tab.playwright.evaluate; it only reads the live DOM.
 * Run on each consumer in light/dark, then inspect again after keyboard focus.
 * Parent performs hover/press and narrow layout checks through normal CUA actions.
 */
export function inspectStateActions() {
  function channels(color) {
    return color.match(/[\d.]+/g).slice(0, 3).map(Number);
  }
  function luminance(rgb) {
    return rgb.map(value => value / 255)
      .map(value => value <= .04045 ? value / 12.92 : ((value + .055) / 1.055) ** 2.4)
      .reduce((sum, value, index) => sum + value * [.2126, .7152, .0722][index], 0);
  }
  function contrast(a, b) {
    const values = [luminance(channels(a)), luminance(channels(b))].sort((a, b) => a - b);
    return (values[1] + .05) / (values[0] + .05);
  }
  function backing(element) {
    for (let node = element; node; node = node.parentElement) {
      const value = getComputedStyle(node).backgroundColor;
      if (value !== 'rgba(0, 0, 0, 0)' && value !== 'transparent') return value;
    }
    return 'rgb(255, 255, 255)';
  }
  return Array.from(document.querySelectorAll('.state-action')).map(element => {
    const style = getComputedStyle(element);
    const background = backing(element);
    const outerBackground = backing(element.parentElement);
    return { id: element.id, text: element.textContent.trim(), disabled: element.disabled,
      pressed: element.getAttribute('aria-pressed'), color: style.color, background,
      boundary: style.borderColor, outerBackground, opacity: style.opacity,
      focus: style.outlineStyle !== 'none' ? `${style.outlineWidth} ${style.outlineColor}` : null,
      focusContrast: style.outlineStyle !== 'none' ? contrast(style.outlineColor, outerBackground) : null,
      inkContrast: contrast(style.color, background), boundaryContrast: contrast(style.borderTopColor, outerBackground),
      hoverInk: style.getPropertyValue('--bs-btn-hover-color').trim(),
      hoverFill: style.getPropertyValue('--bs-btn-hover-bg').trim() };
  });
}

/** Read actual code descendants; syntax colors are reported, never overwritten. */
export function inspectCodeProfile() {
  return Array.from(document.querySelectorAll('main.content div.sourceCode, main.content pre, main.content pre code, main.content pre code span')).map(element => {
    const style = getComputedStyle(element);
    return { tag: element.tagName, id: element.id, classes: element.className,
      fontSize: style.fontSize, lineHeight: style.lineHeight, color: style.color,
      padding: style.padding, fontFamily: style.fontFamily };
  });
}
