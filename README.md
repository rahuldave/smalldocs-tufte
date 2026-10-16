# smalldocs-tufte

A theme that gives a [smalldocs](https://github.com/rahuldave/smalldocs) site, or a
[Quarto](https://quarto.org) site, the look of [Tufte CSS](https://edwardtufte.github.io/tufte-css/).
The text is set in ET Book on a cream paper, in a narrow column. Headings are in
italic, links are underlined in the colour of the text, and tables have only three
rules. The theme has a light mode and a dark mode.

![A page in the Tufte theme](screenshot.png)

## With smalldocs

Add the theme to your project:

```sh
smalldocs add rahuldave/smalldocs-tufte
```

This copies the theme into `_extensions/tufte/`. Then set the theme in `_smalldocs.yml`:

```yaml
theme: tufte
```

In a `_quarto.yml`, put it under `smalldocs:`:

```yaml
smalldocs:
  theme: tufte
```

The site gets both modes, with a button in the navbar that switches between them.
`smalldocs themes` lists the themes of a project, and where each came from.

## With Quarto

```sh
quarto add rahuldave/smalldocs-tufte
```

Then use the format in `_quarto.yml`:

```yaml
format:
  tufte-html:
    toc: true
```

The Quarto theme is the same rules, written as Sass layers in `tufte.scss`
(light) and `tufte-dark.scss` (dark). Quarto follows the mode that the browser
prefers.

## The example

`example/` is a small site that uses the theme. To build it:

```sh
smalldocs add . --dir example
smalldocs render example
```

## What is in the folder

| File | What it is |
|---|---|
| `smalldocs.yml` | The theme for smalldocs: a CSS file for each mode, and the favicon |
| `tufte.css`, `tufte-dark.css` | Bootstrap 5.3.8, then the Tufte rules. smalldocs compiles no Sass, so each file holds all of Bootstrap |
| `_extension.yml`, `tufte.scss`, `tufte-dark.scss` | The theme for Quarto. The fonts are in the Sass file, as data URIs |
| `et-book/` | The ET Book fonts |

## Credits

The look is that of [Tufte CSS](https://github.com/edwardtufte/tufte-css), by Dave
Liepmann and others. The fonts are [ET Book](https://github.com/edwardtufte/et-book),
by Dmitry Krasny, Bonnie Scranton and Edward Tufte. The CSS starts with
[Bootstrap](https://getbootstrap.com/). All three are under the MIT License, and so is
this theme. See [LICENSE](LICENSE).
