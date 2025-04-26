import { GlobalToken, theme } from 'antd';
import Markdown from 'react-markdown';
import rehypeHighlight from 'rehype-highlight';
import rehypeHighlightLines from 'rehype-highlight-code-lines';
import remarkDirective from 'remark-directive';
import remarkGfm from 'remark-gfm';
import remarkGithubAdmonitionsToDirectives from 'remark-github-admonitions-to-directives';
import { css, styled } from 'umi';

type MarkdownProps = {
  children?: string;
};

const StyledMarkdown = styled('div').withConfig({
  shouldForwardProp: (prop) => !['token'].includes(prop),
})<{
  token: GlobalToken;
}>`
  ${({ token }) => {
    return css`
      img {
        max-width: 100%;
      }
      hr {
        border-color: ${token.colorBorderSecondary};
        border-style: solid;
        border-width: 1px;
        border-top: none;
      }
      table {
        display: block;
        overflow: auto;
        margin-block: 24px;
      }
      table th,
      table td {
        border: 1px solid ${token.colorBorderSecondary};
        text-align: left;
        padding: 12px;
      }
      table th p,
      table td p {
        margin: 0;
      }
    `;
  }}
`;

export const ApeMarkdown = ({ children }: MarkdownProps) => {
  const { token } = theme.useToken();
  return (
    <StyledMarkdown token={token}>
      <Markdown
        rehypePlugins={[rehypeHighlight, rehypeHighlightLines]}
        remarkPlugins={[
          remarkGfm,
          remarkGithubAdmonitionsToDirectives,
          remarkDirective,
        ]}
        components={{
          a: (props) => <a {...props} target="_blank" />,
        }}
      >
        {children}
      </Markdown>
    </StyledMarkdown>
  );
};
