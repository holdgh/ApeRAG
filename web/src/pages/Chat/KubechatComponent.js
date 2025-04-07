class kubechatComponent extends HTMLElement {
    constructor() {
        super();
    }

    // Custom Events

    readyEvent = new CustomEvent("ready", {
        bubbles: true, cancelable: false, composed: true
    });

    failedEvent = new CustomEvent("failed", {
        bubbles: true, cancelable: false, composed: true
    });

    openEvent = new CustomEvent("open", {
        bubbles: true, cancelable: false, composed: true
    });

    closeEvent = new CustomEvent("close", {
        bubbles: true, cancelable: false, composed: true
    });

    fullscreenEvent = new CustomEvent("fullscreen", {
        bubbles: true, cancelable: false, composed: true
    });

    questionEvent = new CustomEvent("question", {
        bubbles: true, cancelable: false, composed: true, question: {}
    });

    clearEvent = new CustomEvent("clear", {
        bubbles: true, cancelable: false, composed: true, message: {}
    });

    messageEvent = new CustomEvent("message", {
        bubbles: true, cancelable: false, composed: true, message: {}
    });

    errorEvent = new CustomEvent("error", {
        bubbles: true, cancelable: false, composed: true, message: {}
    });

    streamEvent = new CustomEvent("stream", {
        bubbles: true, cancelable: false, composed: true, message: {}
    });

    welcomeEvent = new CustomEvent("welcome", {
        bubbles: true, cancelable: false, composed: true, message: {}
    });

    beforeSpeakEvent = new CustomEvent("beforeSpeak", {
        bubbles: true, cancelable: true, composed: true, message: {}
    });

    renderEvent = new CustomEvent("render", {
        bubbles: true, cancelable: false, composed: true
    });

    warningMessage = [];

    caption = 'Kubechat';

    logoIcon = 'data:image/svg+xml,%3Csvg viewBox="0 0 1024 1024" version="1.1" xmlns="http://www.w3.org/2000/svg"%3E%3Cpath d="m512,1024a512,512 0 1 1 0,-1024a512,512 0 0 1 0,1024zm-192,-448a64,64 0 1 0 0,-128a64,64 0 0 0 0,128zm192,0a64,64 0 1 0 0,-128a64,64 0 0 0 0,128zm192,0a64,64 0 1 0 0,-128a64,64 0 0 0 0,128z" fill="currentColot" /%3E%3C/svg%3E';

    defaultLogo = 'data:image/svg+xml,%3Csvg viewBox="0 0 1024 1024" version="1.1" xmlns="http://www.w3.org/2000/svg"%3E%3Cpath d="m512,1024a512,512 0 1 1 0,-1024a512,512 0 0 1 0,1024zm-192,-448a64,64 0 1 0 0,-128a64,64 0 0 0 0,128zm192,0a64,64 0 1 0 0,-128a64,64 0 0 0 0,128zm192,0a64,64 0 1 0 0,-128a64,64 0 0 0 0,128z" fill="currentColot" /%3E%3C/svg%3E';

    likeIcon = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg"><text x="50%" y="50%" dominant-baseline="central" text-anchor="middle" font-size="16">👍️</text></svg>';

    dislikeIcon = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg"><text x="50%" y="50%" dominant-baseline="central" text-anchor="middle" font-size="16">👎️</text></svg>';

    getDefaultStyle = () => {
        return `
        :host {
            --primary-color:rgba(124,72,255,1);
            --text-color: rgba(255,255,255,0.65);
            --text-color-tips: rgba(255,255,255,0.2);
            --text-color-score: rgba(255,255,255,0.45);
            --text-color-input: rgba(255,255,255, 0.8);
            --text-color-code: rgba(255,255,255,0.85);
            --text-color-spot: #fff;
            --text-color-question: rgba(255,255,255,0.65);
            --bg-color-logo: #7C48FF;
            --bg-color-bot: rgba(32,33,45,0.5);
            --bg-color-header: rgba(0,0,0,0.5);
            --bg-color-ref: rgba(255,255,255,0.1);
            --bg-color-code: rgba(0,0,0,0.5);
            --bg-color-note: rgba(255,255,255,0.15);
            --bg-color-answer: rgba(255,255,255,0.05);
            --bg-color-ai: rgba(124,72,255,1);
            --bg-color-question: #1B2F60;
            --bg-color-human: #3f3f43;
            --border-color-action: rgba(255,255,255,0.1);
            --border-color-hr: rgba(255,255,255,0.5);
            --topic-shadow: 0 0 15px rgba(0,0,0,0.1);
            --bot-shadow-right: -9px 0 28px 8px rgba(0, 0, 0, 0.5), -6px 0 16px 0 rgba(0, 0, 0, 0.5), -3px 0 6px -4px rgba(0, 0, 0, 0.2);
            --bot-shadow-left: 9px 3px 28px 8px rgba(0, 0, 0, 0.5), 6px 3px 16px 0 rgba(0, 0, 0, 0.5), 3px 3px 6px -4px rgba(0, 0, 0, 0.2);
            --send-display:none;
            --stop-display:none;
        }

        * {
            box-sizing: unset;
            font-size: 14px;
            font-family: monospace, Verdana, Geneva, Tahoma, sans-serif;
            color: var(--text-color);
            margin: 0;
            padding: 0;
        }

        ::-webkit-scrollbar {
            display: none;
        }

        input {
            color: var(--text-color-input);
            background: none;
        }

        input:focus {
            outline-style: none;
            border: 1px solid var(--primary-color);
            box-shadow: 0 0 0 2px rgba(150, 122, 244, 0.18);
        }

        hr {
            border: none;
            height: 1px;
            background: var(--border-color-hr);
            margin: 1rem 0;
        }

        li {
            display: list-item;
        }

        :where(.word,.text) :where(h1,h2,h3,h4,h5,h6):not(:first-child) {
            /*margin: 2rem 0 0.5rem;*/
        }

        :where(.word,.text) h6 {
            font-size: 1rem;
        }

        :where(.word,.text) h5 {
            font-size: 1.1rem;
        }

        :where(.word,.text) h4 {
            font-size: 1.2rem;
        }

        :where(.word,.text) h3 {
            font-size: 1.3rem;
        }

        :where(.word,.text) h2 {
            font-size: 1.4rem;
        }

        :where(.word,.text) h1 {
            font-size: 1.5rem;
        }

        :where(.word,.text) p {
            margin: 0.5rem 0;
            min-height: 0.5rem;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            border: 1px solid var(--bg-color-code);
            position: relative;
            pointer-events: none;
            cursor: copy;
        }
        table::after{
            content: attr(data-copy);
            font-size: 1.8rem;
            position: absolute;
            z-index: 1;
            right: 1rem;
            top: 5px;
            pointer-events: auto;
        }
        table tr:nth-child(odd) {
            background: var(--bg-color-code);
        }
        table .columngroup {
            padding: 0;
            border-top: 1px solid var(--bg-color-code);
            border-bottom: 1px solid var(--bg-color-ref);
        }
        th{
            background: #191A22;
            padding: 0.5rem;
        }
        td{
            padding: 0.5rem;
            font-size: 0.8rem;
        }
        table, th, td {
            border: 1px solid rgba(0,0,0.1);
            text-align: left;
        }
        blockquote {
            padding: 1rem;
            background: var(--bg-color-note);
            border-left: 6px solid var(--text-color-score);
            word-break: break-word;
        }

        /* highlight */
        .html-tag { color: #7EAEF6; }
        .html-attr-name { color:#A6C5F4; }
        .html-attr-value,.css-quote,.es-value,.sql-value { color:#FC8D5F; }
        .html-comment,.css-comment,.es-comment,.sql-comment { color: #8F8F8F; }
        .css-selecter { color: #7CACF2; }
        .css-property { color: #F9CB34; }
        .css-value { color:#C0E8CC; }
        .css-function,.es-keyword,.sql-keyword { color: #BE6DFC;  }
        .es-normal { color: #E1E1E1;  }
        .es-variable { color: #7DADF5; }
        .es-property { color: #F6C934; }

        code {
            background: var(--bg-color-code);
            color: var(--text-color-code);
            border-radius: 4px;
            font-size:100%;
            padding: 0 5px;
            margin: 0 5px;
        }

        pre {
            display: block;
            min-width: 200px;
            background: var(--bg-color-code);
            color: var(--text-color-code);
            padding: 2rem 1rem 1rem;
            margin-bottom:1rem;
            font-size: 0.8rem;
            white-space: break-spaces;
            border-radius: 4px;
            position: relative;
            pointer-events: none;
            cursor: copy;
        }
        pre::before{
            content: attr(data-type);
            display:block;
            pointer-events: none;
            background: linear-gradient(45deg, black, transparent);
            border-radius: 4px 4px 0 0;
            position: absolute;
            width: 100%;
            left: 0;
            top: 0;
            padding: 0.5rem 1rem;
            box-sizing: border-box;
        }
        pre::after{
            content: attr(data-copy);
            font-size: 1.8rem;
            position: absolute;
            z-index: 1;
            right: 1rem;
            top: 5px;
            pointer-events: auto;
        }

        pre span{
            font-size: 0.8rem;
        }
    
        .wrapper {
            position: relative;
        }
    
        .icon {
            display: flex;
            width: 64px;
            height: 64px;
            place-content: center;
            cursor: pointer;
            background:transparent;
            border-radius: 50%;
            position: relative;
        }
    
        .logo {
            width: 100%;
            border-radius: 50%;
            border: none;
            background: url('${this.logoIcon}') center center/100% no-repeat, var(--bg-color-logo);
            display: none;
        }

        .logo.customized{
            background: var(--primary-color);
        }
    
        .bot {
            font-size: 0.8rem;
            min-width: 330px;
            width: 40vw;
            height: 95vh;
            border: 1px solid var(--border-color-action);
            border-radius: 10px;
            background: var(--bg-color-bot);
            display: none;
            position: absolute;
            bottom: 0;
            right: 0;
            z-index: 99999;
            box-shadow: var(--bot-shadow-right);
            transition: all 0.3s ease;
        }
    
        .leftTop{
            top: 0;
            left: 0;
            right: unset;
            bottom: unset;
            box-shadow: var(--bot-shadow-left);
        }
    
        .rightTop{
            top: 0;
            right: 0;
            bottom: unset;
            left: unset;
        }
    
        .rightBottom{
            bottom: 0;
            right: 0;
            top: unset;
            left: unset;
        }
    
        .leftBottom{
            bottom: 0;
            left: 0;
            top: unset;
            right: unset;
            box-shadow: var(--bot-shadow-left);
        }

        .workspace {
            position:relative;
            width: 100%;
            height: 100%;
            border-radius: 10px;
            overflow-x: hidden;
            overflow-y: auto;
            overscroll-behavior: contain;
            -ms-scroll-chaining: contain;
            display: flex;
            flex-flow: column;
        }

        .hd {
            position: sticky;
            top: 0;
            padding: 1rem;
            background: var(--bg-color-header);
            backdrop-filter: blur(18px);
            -webkit-backdrop-filter: blur(18px);
            display: flex;
            justify-content: left;
            align-items: center;
            border-radius: 10px 10px 0 0;
            z-index: 20;
        }

        .hd .title {
            flex: content;
        }

        .hd .action {
            display: flex;
            justify-content: right;
            gap: 5px;
        }

        .hd .action span {
            display: inline-block;
            width: 16px;
            height: 16px;
            line-height: 1;
            text-align: center;
            cursor: pointer;
            background: linear-gradient(0deg, var(--border-color-action), var(--border-color-hr));
            border-radius: 50%;
            transition: all 0.1s ease;
        }

        .hd .action span:hover {
            transform: scale(1.3);
        }

        .bd {
            flex: content;
            padding: 40px 1rem 0;
            backdrop-filter: blur(18px);
            -webkit-backdrop-filter: blur(18px);
        }

        .topic {
            display: flex;
            gap: 10px;
            margin-bottom: 24px;
        }

        .question {
            flex-direction: row-reverse;
        }

        .topic .avatar div {
            width: 32px;
            height: 32px;
            line-height: 34px;
            border-radius: 50%;
            box-shadow: var(--topic-shadow);
        }

        .question .avatar div {
            background: url('${this.avatar}') center center/100% no-repeat, var(--bg-color-human);
        }

        .answer .avatar div {
            background: url('${this.logoIcon}') center center/100% no-repeat, var(--bg-color-ai);
        }

        .topic .word {
            padding: 16px;
            min-height: 18px;
            background: var(--bg-color-answer);
            border-radius: 0 12px 12px;
            box-shadow: var(--topic-shadow);
            word-break: break-word;
            line-height: 1.5rem;
        }
        .topic .word img {
            max-width: 80%;
        }
        .topic .word a {
            color: var(--text-color-spot);
            text-decoration: none;
            margin: 0 4px;
        }
        .topic .word a::after {
            content: "⎘";
            margin-left: 4px;
        }

        .faq {
            display: inline-flex;
            font-style: unset;
            border-radius: 8px;
            padding: 1rem;
            margin: 0.5rem;
            background: var(--bg-color-answer);
            cursor: pointer;
        }

        .related{
            margin-top: 2rem;
            border-top: 1px solid rgba(0,0,0,0.5);
        }

        .related .tips{
            margin: 0;
            padding: 2rem 0.5rem 1rem;
            border-top: 1px solid rgba(255,255,255,0.1);
        }

        .question .word {
            color: var(--text-color-question);
            background: var(--bg-color-question);
            border-radius: 12px 0 12px 12px;
        }

        .topic .info {
            margin-top: 1rem;
            display: flex;
            align-items: center;
            gap: 5px;
        }

        .topic :where(.time, .speaker, .stop-speak, .reference) {
            font-size: 0.6rem;
            padding: 0.5rem;
        }

        .speaker::before{
            content: "🔈";
            color: #fff;
        }

        .stop-speak::before{
            content: "🔇";
            color: #fff;
        }

        .speaker, .stop-speak {
            cursor: pointer;
        }
        
        .invisible {
            display:none!important;
        }

        .topic .reference {
            cursor: pointer;
        }
        .topic .reference::before{
            content: "📖";
            margin-right: 4px;
        }

        .topic .reference .ref-detail{
            display:none;
        }

        .topic .action {
            flex: content;
        }

        .topic .action button {
            visibility: hidden;
            width: 32px;
            height: 32px;
            margin: 0 0 16px;
            border: none;
            cursor: pointer;
        }

        .topic .action:hover button {
            visibility: visible;
        }

        .topic .action .like {
            background: url('${this.likeIcon}') center center/100% no-repeat;
        }

        .topic .action .dislike {
            background: url('${this.dislikeIcon}') center center/100% no-repeat;
        }

        .topic .action .voted {
            background-color: var(--primary-color);
        }

        .ft {
            position: sticky;
            bottom: 0;
            padding: 1rem;
            border-radius: 0 0 10px 10px;
            backdrop-filter: blur(18px);
            -webkit-backdrop-filter: blur(18px);
            z-index: 20;
        }

        .ft .container {
            border-radius: 8px;
            border: 1px solid var(--border-color-action);
        }

        .action-items {
            display: flex;
            margin: 0 1rem 3rem;
            gap: 8px;
            overflow-x: auto;
        }

        .action-item {
            position: relative;
            display: inline-block;
            height: 40px;
        }
        .ft .action-items .action-item::after{
            content: "⨉";
            font-size: 1.5rem;
            cursor: pointer;
            position: absolute;
            display: inline-flex;
            place-content: center;
            align-items: center;
            width: 100%;
            height: 100%;
            color: var(--primary-color);
            left: 0;
            top: 0;
        }

        .ft .tool {
            height: 50px;
            position: absolute;
            right: 20px;
            bottom: 1rem;
            z-index: 9;
            display: inline-flex;
        }

        .ft .tool span{
            display: inline-flex;
            justify-content: center;
            align-items: center;
            width: 32px;
            cursor: pointer;
        }

        .ft .tool .send {
            display: var(--send-display);
        }
        .ft .tool .stop {
            display: var(--stop-display);
        }

        .ft .tool:has(+.talking) {
            --stop-display: inline-flex;
        }

        .ft .tool:has(+.ask input:valid) {
            --send-display: inline-flex;
        }

        .ft .tool label {
            display:inline-block;
            width: 22px;
            height: 22px;
            cursor: pointer;
        }

        .ft .tool svg {
            width: 22px;
            height: 22px;
            pointer-events: none;
        }

        .ft .tool path {
            color: var(--primary-color);
            fill: var(--primary-color);
        }

        .ft .speech.speaking svg {
            border-radius: 50%;
            background: var(--primary-color);
            color: #fff;
        }
        .ft .speech.speaking path {
            color: #fff;
            fill: #fff;
            scale: 80%;
            translate: 10% 10%;
        }

        .ask {
            display: flex;
            width: 100%;
            height: 50px;
            position: relative;
            cursor: pointer;
        }

        .ask input {
            border: none;
            box-shadow: none;
            padding: 1rem ${parseFloat((this.disableSpeech?0:2) + (this.disableUploadImage?0:2) + 2.5)}rem 1rem 1rem;
            width: 100%;
        }

        .ask:has(:not(input:valid, input:focus))::before {
            content: "Enter message...";
            box-sizing: border-box;
            white-space: pre;
            position: absolute;
            display: flex;
            align-items: center;
            z-index: -1;
            left: 0;
            top: 0;
            padding: 0 1rem;
            width: 100%;
            height: 100%;
            color: var(--text-color-tips);
        }

        .ask.tips1:has(:not(input:valid, input:focus))::before {
            content: "Type /clear clear history";
        }

        .ask.tips2:has(:not(input:valid, input:focus))::before {
            content: "Enter message...";
        }

        .ask.tips3:has(:not(input:valid, input:focus))::before {
            content: "[Ctrl + ↵] send message";
        }

        .ask.tips-vision:has(:not(input:valid, input:focus))::before {
            content: "[vision](image url) analyze picture";
        }

        .flying .ask::before {
            content: " ";
            position: absolute;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            border-radius: 8px;
            cursor: default;
            background: var(--bg-color-ref);
        }

        .ext {
            position: absolute;
            right: 0;
            bottom: 1rem;
            z-index: 90;
            width: 50vw;
            height: 50vh;
            overflow-x: hidden;
            overflow-y: auto;
            overscroll-behavior: contain;
            -ms-scroll-chaining: contain;
            border-radius: 10px;
            background: rgba(32,33,45,0.9);
            box-shadow: var(--bot-shadow-right);
            display: none;
            transition: all 0.5s ease;
        }

        .rightTop .ext {
            right: 0;
            top: 1rem;
        }

        .leftTop .ext {
            left: 0;
            top: 1rem;
            box-shadow: var(--bot-shadow-left);
        }

        .leftBottom .ext {
            left: 0;
            bottom: 1rem;
            box-shadow: var(--bot-shadow-left);
        }

        .full-screen .ext {
            width: 50vw;
            height: 100vh;
            top: 0;
        }

        @media (max-width:650px){
            .bot {
                height: calc(70vh - 10px);
            }
            .bot.full-screen {
                height: calc(100vh - 75px);
            }
            .full-screen .ext,.ext {
                width: 80vw;
            }
        }

        .ext .bd {
            padding: 0;
            background: var(--bg-color-bot);
            backdrop-filter: none;
            -webkit-backdrop-filter: none;
        }

        .ext .bd-wrap {
            padding: 24px 1rem;
            margin: 1rem;
            background: var(--bg-color-ref);
            border-radius: 10px;
        }
            
        .ext .title-wrap {
            display: flex;
            height: 28px;
            font-weight: 600;
            align-items: center;
        }
        
        .ext .title-wrap .title{
            flex: content;
            white-space: nowrap;
            text-overflow: ellipsis;
            overflow: hidden;
            text-indent: 5px;
        }
        
        .ext .title-wrap .score{
            color: var(--text-color-score);
            font-weight: 200;
            font-size: 0.8rem;
            white-space: nowrap;
            text-indent: 5px;
        }
        
        .ext .text {
            display: block;
            padding-top: 6px;
            font-size: 0.9rem;
            font-weight: 200;
            word-break: break-word;
        }

        .full-screen {
            position: fixed;
            width: 100vw;
            height: 100vh;
            z-index: 99999;
        }

        .visible {
            display: block;
        }
        
        @keyframes flying {
            0% {
                background-position: -100% 50%;
                background-size: 60%;
            }
            50% {
                background-position: 50% 50%;
                background-size: 60%;
            }
            100% {
                background-position: 250% 50%;
                background-size: 60%;
            }
        }

        .thinking {
            display: inline-block;
            width: 2px;
            height: 15px;
            background: var(--primary-color);
            vertical-align: middle;
            animation: typing 1s linear infinite;
        }

        .thinking i{
            display:none;
        }

        @keyframes typing {
            0%,50% {
                visibility: hidden;
            }
            51%,100% {
                visibility: visible;
            }
        }

        .flying .thinking {
            display: grid;
            width: 50px;
            height: unset;
            grid-template-columns: repeat(5, 1fr);
            justify-items: center;
            column-gap: 5px;
            animation: none;
            background: none;
        }
            
        .flying .thinking i {
            display: inline-flex;
            width: 4px;
            height: 10px;
            border-radius: 1px;
            background: var(--primary-color);
            animation: thinking 1.2s ease-in-out infinite;
        }
            
        .flying .thinking i:nth-child(2) {
            animation-delay: 0.1s;
        }
            
        .flying .thinking i:nth-child(3) {
            animation-delay: 0.2s;
        }
            
        .flying .thinking i:nth-child(4) {
            animation-delay: 0.3s;
        }
            
        .flying .thinking i:nth-child(5) {
            animation-delay: 0.4s;
        }
            
        @keyframes thinking {
            0%,
            40%,
            100% {
                transform: scaleY(1);
            }
            20% {
                transform: scaleY(2.5);
            }
        }

        .waiting{
            position: relative;
            cursor: not-allowed;
            pointer-events: none;
        }

        .waiting * {
            opacity: 0.6;
        }

        .waiting::before {
            content: "";
            backdrop-filter: blur(1px);
            -webkit-backdrop-filter: blur(1px);
            position: absolute;
            display: flex;
            z-index: 1;
            width: 100%;
            height: 100%;
        }

        .waiting::after {
            content: "";
            display: inline-flex;
            width: 16px;
            height: 16px;
            border-radius: 50%;
            border: 2px solid rgba(255, 255, 255, 50%);
            border-color: var(--primary-color) transparent var(--primary-color) transparent;
            position: absolute;
            left: calc(50% - 10px);
            top: calc(50% - 10px);
            z-index: 2;
            animation: waiting 2s linear infinite;
        }

        .warning::before {
            background: rgba(0,0,0,0.8);
            border-radius: 50%;
            cursor: not-allowed;
            pointer-events: visible;
        }
        .warning::after {
            content: "🚫";
            width: 32px;
            height: 32px;
            line-height: 22px;
            left: 0;
            top: calc(50% - 9px);
            font-size: 4rem;
            color: red;
            border: none;
            border-radius: 0;
            animation: none;
        }

        @keyframes waiting {
            0% {
                transform: rotate(0deg);
            }
            
            100% {
                transform: rotate(360deg);
            }
        }

        /* offstage mode */
        .offstage {
            display: none;
        }

        /* adaptive mode */
        .adaptive .icon {
            display: none;
        }

        .adaptive .action .close {
            display: none;
        }

        .adaptive .ext .hd .action .close {
            display: inline-block;
        }

        .adaptive .bot {
            display: block;
            width: 100%;
        }

        .adaptive .warning::before {
            background: none;
            border-radius: none;
        }

        .adaptive .warning::after {
            content: attr(title);
            border: none;
            animation: none;
            width: 50%;
            height: unset;
            line-height: unset;
            font-size: unset;
            color: var(--text-color-score);
            left: 25%;
            overflow:hidden;
        }

        /* Customized Style */
        ${this.customStyle}
        `;
    }

    // Detect bot position
    detectPosition = (dom) =>{
        const l = dom.offsetLeft, t = dom.offsetTop, w = window.innerWidth, h =window.innerHeight;
        const pos = {
            '00': 'leftTop',
            '01': 'leftBottom',
            '10': 'rightTop',
            '11': 'rightBottom',
        }
        const il = (l>w/2)?'1':'0';
        const bl = (t>h/2)?'1':'0';
        return pos[il+bl];
    }

    // Update bot position
    updateBotPosition = () => {
        const pos = this.detectPosition(this.parentNode);
        this.bot.classList.remove('leftTop', 'leftBottom', 'rightTop', 'rightBottom');
        this.bot.classList.add(pos);
    }

    // Display bot or not
    setBotExpand = (bShow) => {
        if(!this.readyToGo){
            console.log('The chat bot is not ready, please check the messages in the console.');
            return;
        }
        if(bShow){
            this.updateBotPosition();
            this.botExpand = true;
            this.bot.classList.add('visible');
            this.logo.classList.remove('visible');
            const workspace = this.chatDom.parentNode;
            workspace.scrollTop = workspace.scrollHeight;
            this.dispatchEvent(this.openEvent);
        }else{
            this.botExpand = false;
            this.bot.classList.remove('visible');
            this.logo.classList.add('visible');
            this.dispatchEvent(this.closeEvent);
        }
    }

    setChatWaiting = (bWaiting) => {
        if(bWaiting){
            this.waiting = true;
            this.bot.classList.add('flying');
        }else{
            this.waiting = false;
            this.bot.classList.remove('flying');
        }
    }

    // Show reference
    showReference = (ref)=>{
        const bot = this.bot;
        const w = bot.offsetWidth;
        const h = bot.offsetHeight;
        const l = window.innerWidth - w;
        const t = window.innerHeight - h;

        const reference = this.refDom;
        if(!reference){return;}
        if(ref){
            const extbd = reference.getElementsByClassName('ext-bd')[0];
            if(extbd){
                extbd.innerHTML = ref;
            }
            reference.style.left = '0';
            reference.style.top = '0';
            reference.style.width = w+'px';
            reference.style.height = h+'px';
            reference.classList.add('visible');
            const exthd = reference.getElementsByClassName('hd')[0];
            exthd.scrollIntoView({behavior:'instant', block:'start'});
            reference.scrollTop = 0;
        }else{
            reference.classList.remove('visible');
            const workspace = this.chatDom.parentNode;
            workspace.scrollTop = workspace.scrollHeight;
        }
    }

    // Toggle fullscreen
    toggleFullScreen = () => {
        this.bot.classList.toggle('full-screen');
        this.isFullScreen = this.bot.classList.contains('full-screen');
        if(this.isFullScreen){
            this.dispatchEvent(this.fullscreenEvent);
        }
    }

    // Update Caption
    updateCaption = (caption) => {
        const title = caption || this.getAttribute("caption");
        if(title){
            this.caption = title
            const domHeader = this.bot.getElementsByClassName('title')[0];
            if(domHeader){
                domHeader.textContent = title;
            }
        }
    }

    // Cookie
    getCookie =(key) => {
        return document.cookie.replace(
            new RegExp("(?:(?:^|.*;\\s*)" + key + "\\s*\\=\\s*([^;]*).*$)|^.*$"),
            "$1"
        );
    }

    setCookie = (key, value) => {
        document.cookie = `${key}=${value}`;
    }

    // Util
    templateReplace = (template, replacements) => {
        return template.replace(/\${(.*?)}/g, (match, name) => {
          return replacements.hasOwnProperty(name) ? replacements[name] : match;
        });
    }

    getLang = (text) => {
        const len = (s, r) => {
          return s.match(r)?.length||0;
        }
        const langs = {
          "en": (x)=>len(x, /([a-zA-Z])/g),
          "zh": (x)=>len(x, /([a-zA-Z\u4e00-\u9fa5])/g),
          "ja": (x)=>len(x, /([\u3040-\u309f\u30a0-\u30ff\u31f0-\u31ff])/g),
          "ko": (x)=>len(x, /([\uac00-\ud7af])/g),
          "ru": (x)=>len(x, /([а-яА-Я])/g),
        };
        const lang = Object.entries(langs).reduce((pre, cur)=>{
            return (cur[1](text) > pre[1](text)) ? cur : pre;
        });
        const langDefault = window.navigator.language || window.navigator.userLanguage;
        return lang[0]||langDefault;
    }
      
    speak = (text, fnOnEnd) => {
        const utterance = new SpeechSynthesisUtterance();
        utterance.onend = () => {
            if(typeof fnOnEnd === 'function'){
                fnOnEnd();
            }
        }
        utterance.text = text;
        utterance.lang = this.getLang(text);
        window.speechSynthesis.speak(utterance);
    }

    stopSpeak = () => {
        window.speechSynthesis.cancel();
    }

    initSpeechRecognition = () => {
        const input = this.input || this.bot.getElementsByClassName('input')[0];
        const that = this;
        const recognition = new webkitSpeechRecognition();
        recognition.lang = 'zh-CN'; // 设置语言
        recognition.continuous = true; // 设置是否连续识别
        recognition.interimResults = true; // 设置是否返回临时结果
        recognition.go = function(speechDom){
            this.speechDom = speechDom;
            this.speechDom.classList.add('speaking');
            this.start();
        }
        recognition.onstart = function() {
            // console.log('语音识别已开始');
        };
        recognition.onerror = function(event) {
            // console.error('语音识别错误:', event.error);
            if(this.speechDom){
                this.speechDom.classList.remove('speaking')
            }
        };
        recognition.onresult = function(event) {
            if (event.results[0].isFinal) {
                const result = event.results[0][0].transcript;
                switch(result){
                    case '清空聊天记录':
                    case '删除聊天记录':
                    case 'clear chat history':
                        that.askQuestion('/clear');
                        break;
                    default:
                        // that.askQuestion(event.results[0][0].transcript);
                        input.value = event.results[0][0].transcript;
                        break;
                }
                this.stop();
            }else{
                input.value = event.results[0][0].transcript; // 将识别结果显示在输入框中
            }
        };
        recognition.onend = function() {
            // console.log('语音识别已结束');
            if(this.speechDom){
                this.speechDom.classList.remove('speaking')
            }
        };
        return recognition;
    }

    tagFree = (str) => {
        return str.replace(/&/g,'&amp;')
        .replace(/(<)|>/g, (m,a)=>a?'&lt;':'&gt;');
    }

    trim = (s) => s.replace(/^\s+|\s+$/,'');

    timestampToTime = (timestamp) => {
        if(!timestamp){return '';}
        let date = new Date(timestamp);
        let Y = date.getFullYear() + "-";
        let M =
            (date.getMonth() + 1 < 10
            ? "0" + (date.getMonth() + 1)
            : date.getMonth() + 1) + "-";
        let D = date.getDate();
        if(D<10){D = '0' + D;}
        let h = date.getHours();
        if(h<10){h = '0' + h;}
        let m = date.getMinutes();
        if(m<10){m = '0' + m;}
        let s = date.getSeconds();
        if(s<10){s = '0' + s;}
        return Y + M + D + ' ' + h + ':' + m + ':' + s;
    }

    copyText = (dom) => {
        if(!dom){return;}
        const textarea = document.createElement('textarea');
        textarea.value = dom.innerText;
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand('copy');
        document.body.removeChild(textarea);
    }

    StateMachine = (rules) => {
        const machine = function(rules){
            this.rules = rules;
        };
        machine.prototype.gothrough = function (code) {
            let currentState = 'STATE_NORMAL';
            let token = '', result = '';
            let state = {}, pair = {};
            //scan through every character
            for (let i = 0; i < code.length; i++) {
                let char = code[i], pre = code[i-1], next = code[i+1], processedChar;
                let rule = this.rules[currentState];
                let nextState = currentState;
                let nestState = false;
                let stateUpdate = false;
                //state match
                for (let transition of rule.transitions) {
                    let pairChar = pair[currentState]?.slice(-1)[0];
                    //enter state
                    if (transition.condition({char, pre, next, pairChar})) {
                        let toState = transition.toState;
                        if(typeof toState === 'function'){
                            toState = toState(token, currentState);
                        }
                        if(typeof toState === 'string' && !pair[toState]){
                            pair[toState] = [];
                        }
                        if(typeof transition.charProcessor === 'function'){
                            processedChar = transition.charProcessor(char);
                        }
                        if(typeof transition.tokenProcessor === 'function'){
                            result += transition.tokenProcessor(token, currentState, toState);
                            token = '';
                        }
                        if(rule.entryToken){
                            result += rule.entryToken;
                        }
                        if(typeof transition.charStep === 'number'){
                            i += transition.charStep;
                        }
                        nextState = toState;
                        stateUpdate = true;
                        nestState = transition.nestState;
                        if(typeof nextState==='string'){
                            let pairchar = char;
                            if(typeof transition.pairChar === 'function'){
                                pairchar = transition.pairChar({char, pre, next});
                            }
                            if(nestState){
                                if(!state[nextState]){state[nextState]=[];}
                                state[nextState].push(currentState);
                                pair[nextState]?.push(pairchar);
                            }else{
                                pair[nextState]?.pop();
                                pair[nextState]?.push(pairchar);
                            }
                        }
                        break;
                    }
                }
                //exit state
                if (nestState || nextState !== currentState) {
                    if(rule.tokenProcessor){
                        result += rule.tokenProcessor(char, token);
                    }else{
                        result += token;
                    }
                    if (rule.exitToken) {
                        result += rule.exitToken;
                    }
                    stateUpdate = true;
                    if(nextState===-1){
                        nextState = state[currentState]?.pop() || 'STATE_NORMAL';
                        pair[currentState]?.pop();
                    }
                    if(nextState){
                        currentState = nextState;
                    }
                }
                //handle condition character
                if(rule.charProcessor){
                    char = rule.charProcessor(char);
                }
                if(stateUpdate){
                    result += processedChar == null ? char : processedChar;
                    token = '';
                }else{
                    token += char;
                }
            }
            //last state token closure
            let rule = this.rules[currentState];
            if (rule.entryToken) {
                result += rule.entryToken;
            }
            if(rule.tokenProcessor){
                result += rule.tokenProcessor(token, currentState);
            }else{
                result += token;
            }
            if (rule.exitToken) {
                result += rule.exitToken;
            }
            return result;
        };
        return new machine(rules);
    }

    // YAML Machine
    yamlMachine = () => {
        const tagFree = this.tagFree, trim = this.trim;
        const Rules = {
            STATE_NORMAL: {
                transitions: [
                    {
                    condition: (o) => o.char === '-' && /\s/.test(o.next),
                    toState: 'STATE_BRANCH',
                    },
                    {
                    condition: (o) => o.char === '-' && /\s/.test(o.pre) && /[a-zA-Z]/.test(o.next),
                    toState: 'STATE_VALUE',
                    charProcessor: (char)=>`<span class="es-value">${char}</span>`,
                    },
                    {
                    condition: (o) => o.char === ':',
                    toState: 'STATE_VALUE',
                    },
                    {
                    condition: (o) => o.char === '#',
                    toState: 'STATE_COMMENT',
                    charProcessor: (char)=>`<span class="es-comment">${char}</span>`,
                    },
                ],
                entryToken: `<span class="css-selecter ">`,
                exitToken: `</span>`,
                charProcessor: tagFree,
            },
            STATE_BRANCH: {
                transitions: [
                    {
                    condition: (o) => o.char===':' && /\s/.test(o.next),
                    tokenProcessor: (token)=>`<span class="css-selecter">${token}</span>`,
                    toState: 'STATE_VALUE',
                    },
                    {
                    condition: (o) => o.char==='\n',
                    tokenProcessor: (token)=>`<span class="es-value">${token}</span>`,
                    toState: 'STATE_NORMAL',
                    },
                    {
                    condition: (o) => o.char === '#',
                    toState: 'STATE_COMMENT',
                    nestState: true,
                    charProcessor: (char)=>`<span class="es-comment">${char}</span>`,
                    },
                ],
                entryToken: `<span class="es-value">`,
                exitToken: `</span>`,
                charProcessor: tagFree,
            },
            STATE_VALUE: {
                transitions: [
                    {
                    condition: (o) => o.char==='\n' && o.pre!=='|',
                    toState: 'STATE_NORMAL',
                    },
                    {
                    condition: (o) => o.char === '"' || o.char === "'" || o.char=== "`",
                    toState: 'STATE_QUOTE',
                    nestState: true,
                    charProcessor:(char)=> `<span class="es-value">${char}</span>`,
                    },
                    {
                    condition: (o) => o.char === '#',
                    toState: 'STATE_COMMENT',
                    nestState: true,
                    charProcessor: (char)=>`<span class="es-comment">${char}</span>`,
                    },
                ],
                entryToken: `<span class="es-value">`,
                exitToken: `</span>`,
                charProcessor: tagFree,
            },
            STATE_QUOTE: {
                transitions: [
                    {
                    condition: (o) => o.char===o.pairChar && o.pre!=='\\',
                    toState: -1,
                    charProcessor:(char)=> `<span class="es-value">${char}</span>`,
                    },
                ],
                entryToken: `<span class="es-value">`,
                exitToken: `</span>`,
                charProcessor: (char)=>tagFree(char),
            },
            STATE_COMMENT: {
                transitions: [
                    {
                    condition: (o) => o.char === '\n',
                    toState: -1,
                    },
                ],
                entryToken: `<span class="es-comment">`,
                exitToken: `</span>`,
                charProcessor: tagFree,
            },
        }
        const yamlMachine = this.StateMachine(Rules);
        return yamlMachine;
    }

    // SQL Machine
    sqlMachine = () => {
        const KEYWORDS = [
            'AUTO_INCREMENT', 'AUTOINCREMENT', 'TIMESTAMPDIFF', 'DATE_FORMAT', 'TRANSACTION', 'CONSTRAINT', 
            'REFERENCES', 'PROCEDURE', 'SUBSTRING', 'SAVEPOINT', 'IDENTITY', 'SEQUENCE','DATABASE', 'DISTINCT', 'TRUNCATE',                    
            'COALESCE', 'DATEDIFF', 'ROLLBACK', 'BETWEEN', 'DEFAULT', 'FOREIGN', 'PRIMARY', 'BACKUP', 'COLUMN', 'CREATE', 
            'DELETE', 'EXISTS', 'HAVING', 'INSERT', 'ROWNUM', 'SELECT', 'SERIAL', 'COMMIT', 'UNIQUE', 'UPDATE', 'VALUES', 'LENGTH', 
            'CONCAT', 'IFNULL', 'NULLIF', 'ALTER', 'CHECK', 'BEGIN', 'GROUP', 'INDEX', 'INNER', 'LIMIT', 'ORDER', 'OUTER', 'RIGHT', 
            'TABLE', 'UNION', 'WHERE', 'COUNT', 'UPPER', 'LOWER', 'ROUND', 'CASE', 'DESC', 'DROP', 'EXEC', 'FROM', 'FULL', 'INTO', 
            'JOIN', 'WORK', 'LEFT', 'LIKE', 'NULL', 'VIEW', 'CAST', 'CASE', 'SHOW', 'ADD', 'ALL', 'AND', 'ANY', 'ASC', 'KEY', 'END',
            'NOT', 'SET', 'TOP', 'AVG', 'SUM', 'MIN', 'MAX', 'NOW', 'SET', 'AS', 'IN', 'IS', 'OR', 'BY', 'GO', 'ON'
        ];
        const tagFree = this.tagFree, trim = this.trim;
        const isKeyword = (s)=>KEYWORDS.includes(trim(s.toUpperCase()));
        const Key = (token)=>{
            if(isKeyword(token)){
                return `<span class="sql-keyword">${token}</span>`;
            }else{
                return token;
            }
        }
        const Rules = {
            STATE_NORMAL: {
                transitions: [
                    {
                    condition: (o) => /[\s,;\(]/.test(o.char),
                    tokenProcessor: Key,
                    },
                    {
                    condition: (o) => o.char === '"' || o.char === "'" || o.char=== "`",
                    toState: 'STATE_VALUE',
                    charProcessor: (char)=>`<span class="sql-value">${char}</span>`,
                    },
                    {
                    condition: (o) => o.char === '-' && o.next === '-',
                    toState: 'STATE_COMMENT',
                    charProcessor: (char)=>`<span class="sql-comment">${char}</span>`,
                    },
                ],
                charProcessor: tagFree,
            },
            STATE_VALUE: {
                transitions: [
                    {
                    condition: (o) => o.char===o.pairChar && o.pre!=='\\',
                    toState: 'STATE_NORMAL',
                    charProcessor: (char)=>`<span class="sql-value">${char}</span>`,
                    },
                ],
                entryToken: `<span class="sql-value">`,
                exitToken: `</span>`,
                charProcessor: tagFree,
            },
            STATE_COMMENT: {
                transitions: [
                    {
                    condition: (o) => o.char === '\n',
                    toState: 'STATE_NORMAL',
                    },
                ],
                entryToken: `<span class="sql-comment">`,
                exitToken: `</span>`,
                charProcessor: tagFree,
            },
        }
        const sqlMachine = this.StateMachine(Rules);
        return sqlMachine;
    }

    // CSS Machine
    cssMachine = () => {
        const tagFree = this.tagFree, trim = this.trim;
        const Rules = {
            STATE_NORMAL: {
                transitions: [
                    {
                    condition: (o) => o.char === '{' || o.char === '(',
                    toState: 'STATE_CSS_PROPERTY',
                    },
                    {
                    condition: (o) => o.char === '/' && o.next === '*',
                    toState: 'STATE_COMMENT',
                    charProcessor: (char)=>`<span class="css-comment">/</span>`,
                    },
                ],
                entryToken: `<span class="css-selecter">`,
                exitToken: `</span>`,
                charProcessor: tagFree,
            },
            STATE_CSS_PROPERTY: {
                transitions: [
                    {
                    condition: (o) => o.char === '{',
                    toState: 'STATE_CSS_PROPERTY',
                    nestState: true,
                    tokenProcessor: (token)=>`<span class="css-selecter">${token}</span>`,
                    },
                    {
                    condition: (o) => o.char === '}',
                    toState: 'STATE_NORMAL',
                    },
                    {
                    condition: (o) => o.char === ';',
                    },
                    {
                    condition: (o) => o.char === ':',
                    toState: 'STATE_CSS_VALUE',
                    nestState: true,
                    },
                    {
                    condition: (o) => o.char === '/' && o.next === '*',
                    toState: 'STATE_COMMENT',
                    nestState: true,
                    charProcessor: (char)=>`<span class="css-comment">/</span>`,
                    },
                ],
                entryToken: `<span class="css-property">`,
                exitToken: `</span>`,
                charProcessor: tagFree,
            },
            STATE_CSS_VALUE: {
                transitions: [
                    {
                    condition: (o) => o.char === ';' || o.char === ')',
                    toState: -1,
                    },
                    {
                    condition: (o) => o.char === ' ',
                    },
                    {
                    condition: (o) => o.char === '}',
                    toState: 'STATE_NORMAL',
                    },
                    {
                    condition: (o) => o.char === '"' || o.char === "'" || o.char=== "`",
                    toState: 'STATE_CSS_QUOTE',
                    nestState: true,
                    charProcessor: (char)=>`<span class="css-quote">${char}</span>`,
                    },
                    {
                    condition: (o) => o.char === '(',
                    toState: 'STATE_CSS_VALUE',
                    nestState: true,
                    tokenProcessor: (token)=>`<span class="css-function">${token}</span>`,
                    },
                    {
                    condition: (o) => o.char === '/' && o.next === '*',
                    toState: 'STATE_COMMENT',
                    nestState: true,
                    charProcessor: (char)=>`<span class="css-comment">/</span>`,
                    },
                ],
                entryToken: `<span class="css-value">`,
                exitToken: `</span>`,
                charProcessor: tagFree,
            },
            STATE_CSS_QUOTE: {
                transitions: [
                    {
                    condition: (o) => o.char===o.pairChar && o.pre!=='\\',
                    toState: -1,
                    charProcessor: (char)=>`<span class="css-quote">${char}</span>`,
                    },
                ],
                entryToken: `<span class="css-quote">`,
                exitToken: `</span>`,
                charProcessor: tagFree,
            },
            STATE_COMMENT: {
                transitions: [
                    {
                    condition: (o) => o.char === '/',
                    toState: -1,
                    charProcessor: (char)=>`<span class="css-comment">/</span>`,
                    },
                ],
                entryToken: `<span class="css-comment">`,
                exitToken: `</span>`,
                charProcessor: tagFree,
            },
        }
        const cssMachine = this.StateMachine(Rules);
        return cssMachine;
    }
    
    // ES Machine (common language)
    esMachine = (language) => {
        const tagFree = this.tagFree, trim = this.trim;
        const KEYWORDS = new Set([
            //es keywords
            'instanceof', 'implements', 'interface', 'protected', 'continue', 'debugger', 'function', 
            'default', 'extends', 'finally', 'package', 'private', 'delete', 'export', 'import', 'return', 
            'switch', 'typeof', 'public', 'static', 'break', 'catch', 'class', 'const', 'super', 'throw', 
            'while', 'yield', 'await', 'false', 'case', 'else', 'this', 'void', 'with', 'enum', 'null', 
            'true', 'for', 'let', 'new', 'try', 'var', 'do', 'if', 'in',
            //python keywords
            'continue', 'nonlocal', 'finally', 'assert', 'except', 'global', 'import', 'lambda', 'return', 'False', 
            'async', 'await', 'break', 'class', 'raise', 'while', 'yield', 'None', 'True', 'elif', 'else', 'from', 
            'pass', 'with', 'and', 'def', 'del', 'for', 'not', 'try', 'as', 'if', 'in', 'is', 'or',
            //go keywords
            'fallthrough', 'interface', 'continue', 'default', 'package', 'select', 'struct', 'switch', 'import', 
            'return', 'break', 'defer', 'const', 'range', 'func', 'case', 'chan', 'else', 'goto', 'type', 'map', 
            'for', 'var', 'go', 'if',
            //java keywords
            'synchronized', 'implements', 'instanceof', 'interface', 'protected', 'transient', 'abstract', 'continue', 
            'strictfp', 'volatile', 'boolean', 'default', 'extends', 'finally', 'package', 'private', 'assert', 'double', 
            'import', 'native', 'public', 'return', 'static', 'switch', 'throws', 'break', 'catch', 'class', 'const', 
            'final', 'float', 'short', 'super', 'throw', 'while', 'byte', 'case', 'char', 'else', 'enum', 'goto', 'long', 
            'this', 'void', 'for', 'int', 'new', 'try', 'do', 'if',
            //c keywords
            'continue', 'register', 'volatile', 'restrict', 'unsigned', 'typedef', 'default', 'sizeof', 'static', 
            'extern', 'return', 'struct', 'switch', 'double', 'inline', 'const', 'float', 'short', 'union', 'while', 
            'break', 'else', 'long', 'case', 'enum', 'goto', 'void', 'char', 'auto', 'int', 'for', 'do', 'if',
            //c# keywords
            'stackalloc', 'interface', 'namespace', 'protected', 'unchecked', 'abstract', 'continue', 'delegate', 
            'explicit', 'implicit', 'internal', 'operator', 'override', 'readonly', 'volatile', 'checked', 'decimal', 
            'default', 'finally', 'foreach', 'private', 'virtual', 'double', 'extern', 'object', 'params', 'public', 
            'return', 'sealed', 'sizeof', 'static', 'string', 'struct', 'switch', 'typeof', 'unsafe', 'ushort', 'break', 
            'catch', 'class', 'const', 'event', 'false', 'fixed', 'float', 'sbyte', 'short', 'throw', 'ulong', 'using', 
            'while', 'base', 'bool', 'byte', 'case', 'char', 'else', 'enum', 'goto', 'lock', 'long', 'null', 'this', 
            'true', 'uint', 'void', 'for', 'int', 'new', 'out', 'ref', 'try', 'as', 'do', 'if', 'in', 'is',
            //php keywords
            'include_once', 'require_once', 'enddeclare', 'endforeach', 'implements', 'instanceof', 'endswitch', 'insteadof', 
            'interface', 'namespace', 'protected', 'abstract', 'callable', 'continue', 'endwhile', 'function', 'declare', 
            'default', 'extends', 'finally', 'foreach', 'include', 'private', 'require', 'elseif', 'endfor', 'global', 'public', 
            'return', 'static', 'switch', 'array', 'break', 'catch', 'class', 'clone', 'const', 'empty', 'endif', 'final', 'isset', 
            'print', 'throw', 'trait', 'unset', 'while', 'yield', 'case', 'echo', 'else', 'eval', 'exit', 'goto', 'list', 'and', 
            'die', 'for', 'new', 'try', 'use', 'var', 'xor', 'as', 'do', 'if', 'or',
            //asp, vb keywords
            'GetXMLNamespace','NotInheritable','NotOverridable','RemoveHandler','MustOverride','MustInherit','Overridable','AddHandler',
            'DirectCast','Implements','ParamArray','RaiseEvent','WithEvents','AddressOf','Interface','Namespace','Narrowing','Overloads',
            'Overrides','Protected','Structure','WriteOnly','Continue','Delegate','Function','Inherits','Operator','Optional','Property',
            'ReadOnly','SyncLock','UInteger','Widening','#ElseIf','AndAlso','Boolean','CUShort','Decimal','Declare','Default','Finally',
            'GetType','Handles','Imports','Integer','MyClass','Nothing','Partial','Private','Shadows','TryCast','Variant','#Const','CSByte',
            'CShort','Double','ElseIf','Friend','Global','Module','MyBase','Object','Option','OrElse','Public','Resume','Return','Select',
            'Shared','Single','Static','String','TypeOf','UShort','#Else','Alias','ByRef','ByVal','Catch','CBool','CByte','CChar','CDate',
            'Class','Const','CType','CUInt','CULng','Erase','Error','Event','False','GoSub','IsNot','ReDim','SByte','Short','Throw','ULong',
            'Using','While','#End','Byte','Call','Case','CDbl','CDec','Char','CInt','CLng','CObj','CSng','CStr','Date','Each','Else','Enum',
            'Exit','GoTo','Like','Long','Loop','Next','Step','Stop','Then','True','Wend','When','With','#If','And','Dim','End','For','Get',
            'Let','Lib','Mod','New','Not','REM','Set','Sub','Try','Xor','As','Do','If','In','Is','Me','Of','On','Or','To'
        ]);
        const isKeyword = (s)=>KEYWORDS.has(trim(s));
        const isVariable = (s)=>(/^[\$_A-Za-z][\$_A-Za-z0-9]*$/.test(s));
        const K = (token)=>{
            if(isKeyword(token)){
                return `<span class="es-keyword">${token}</span>`;
            }else{
                return token;
            }
        }
        const KP = (token)=>{
            if(isKeyword(token)){
                return `<span class="es-keyword">${token}</span>`;
            }else if(isVariable(token)){
                return `<span class="es-property">${token}</span>`;
            }else{
                return token;
            }
        }
        const KV = (token)=>{
            if(isKeyword(token)){
                return `<span class="es-keyword">${token}</span>`;
            }else if(isVariable(token)){
                return `<span class="es-variable">${token}</span>`;
            }else{
                return token;
            }
        }
        const Rules = {
            STATE_NORMAL: {
                transitions: [
                    {
                    condition: (o) => o.char === ':' && o.next!=='\n',
                    tokenProcessor: (token)=>KP(token),
                    },
                    {
                    condition: (o) => !['$',':','.','"',"'","`",'/','#'].includes(o.char) && /\W/.test(o.char),
                    tokenProcessor: (token)=>KV(token),
                    },
                    {
                    condition: (o) => o.char === '.' && !/[\d\\]/.test(o.pre),
                    toState: 'STATE_ES_PROPERTY',
                    },
                    {
                    condition: (o) => o.char === '"' || o.char === "'" || o.char=== "`",
                    toState: 'STATE_ES_VALUE',
                    charProcessor:(char)=> `<span class="es-value">${char}</span>`,
                    },
                    {
                    condition: (o) => o.char === '/'  && o.next !== '/' && o.next !== '*',
                    toState: 'STATE_ES_REGEXP',
                    },
                    {
                    condition: (o) => o.char === '/'  && (o.next === '/' || o.next === '*'),
                    toState: 'STATE_ES_COMMENT',
                    pairChar: (o) => o.next,
                    charProcessor: (char)=>`<span class="es-comment">${char}</span>`,
                    },
                ],
                charProcessor: (char)=>tagFree(char),
            },
            STATE_ES_PROPERTY: {
                transitions: [
                    {
                    condition: (o) => o.char === '.',
                    },
                    {
                    condition: (o) => o.char !== '.' && /\W/.test(o.char),
                    toState: 'STATE_NORMAL',
                    },
                    {
                    condition: (o) => o.char === '/'  && (o.next === '/' || o.next === '*'),
                    toState: 'STATE_ES_COMMENT',
                    nestState: true,
                    pairChar: (o) => o.next,
                    charProcessor: (char)=>`<span class="es-comment">${char}</span>`,
                    },
                    {
                    condition: (o) => o.char === '#',
                    toState: 'STATE_ES_COMMENT',
                    nestState: true,
                    pairChar: (o) => o.next,
                    charProcessor: (char)=>`<span class="es-comment">${char}</span>`,
                    },
                ],
                entryToken: `<span class="es-property">`,
                exitToken: `</span>`,
                charProcessor: (char)=>tagFree(char),
            },
            STATE_ES_VALUE: {
                transitions: [
                    {
                    condition: (o) => o.char===o.pairChar && o.pre!=='\\',
                    toState: -1,
                    charProcessor:(char)=> `<span class="es-value">${char}</span>`,
                    },
                ],
                entryToken: `<span class="es-value">`,
                exitToken: `</span>`,
                charProcessor: (char)=>tagFree(char),
            },
            STATE_ES_REGEXP: {
                transitions: [
                    {
                    condition: (o) => o.char==='/' && o.pre!=='\\' && o.next!=='/',
                    toState: -1,
                    },
                    {
                    condition: (o) => o.char==='/' && o.pre!=='\\' && o.next=='/',
                    toState: -1,
                    charStep: -1,
                    charProcessor: (char)=>``,
                    tokenProcessor: (token)=>`</span>${token}`,
                    },
                    {
                    condition: (o) => o.char==='\n',
                    toState: -1,
                    tokenProcessor: (token)=>`</span>${token}`,
                    },
                ],
                entryToken: `<span class="es-value">`,
                exitToken: `</span>`,
                charProcessor: (char)=>tagFree(char),
            },
            STATE_ES_COMMENT: {
                transitions: [
                    {
                    condition: (o) => o.char==='/' && o.pre==='*',
                    toState: -1,
                    charProcessor: (char)=>`<span class="es-comment">${char}</span>`,
                    },
                    {
                    condition: (o) => o.char==='\n' && o.pairChar!=='*',
                    toState: -1,
                    },
                ],
                entryToken: `<span class="es-comment">`,
                exitToken: `</span>`,
                charProcessor: (char)=>tagFree(char),
            },
        }
        if(language){
            const languageRule = {};
            languageRule['python'] = {
                STATE_NORMAL:{
                    transitions:[
                        {
                        condition: (o) => o.char === ':' && o.next==='\n',
                        tokenProcessor: (token)=>K(token),
                        },
                        {
                        condition: (o) => o.char === '/'  && (o.pre === '/'||o.next === '/'),
                        toState: -1,
                        },
                        {
                        condition: (o) => o.char === '#',
                        toState: 'STATE_ES_COMMENT',
                        pairChar: (o) => o.next,
                        charProcessor: (char)=>`<span class="es-comment">${char}</span>`,
                        },
                    ]
                }
            }
            languageRule['vb'] = {
                STATE_NORMAL:{
                    transitions:[
                        {
                        condition: (o) => o.char === "'",
                        toState: 'STATE_ES_COMMENT',
                        pairChar: (o) => o.next,
                        charProcessor: (char)=>`<span class="es-comment">${char}</span>`,
                        },
                    ]
                }
            }
            Rules.STATE_NORMAL.transitions = [...(languageRule[language]?.STATE_NORMAL.transitions||[]), ...Rules.STATE_NORMAL.transitions];
        }
        const esMachine = this.StateMachine(Rules);
        return esMachine;
    }
    
    // HTML Machine
    htmlMachine = () => {
        const tagFree = this.tagFree, trim = this.trim;
        let BRANCH = [];
        const ESMachine = this.esMachine();
        const CSSMachine = this.cssMachine();
        const getBranch = function(code){
                const css = /(<style[^>]*>)((?:\n*[^\n]*?)+?)(<\/style>)/gi;
                const script = /(<script[^>]*>)((?:\n*[^\n]*?)+?)(<\/script>)/gi;
                const process = function(s, rule, fn){
                    if(typeof fn !=='function'){
                        fn=(i)=>i;
                    }
                    return s.replace(rule, (m,a,b,c)=>{
                        BRANCH.push(fn(b));
                        return `${a}\${${BRANCH.length-1}}${c}`});
                }
                code = process(code, script, (i)=>ESMachine.gothrough(i));
                code = process(code, css, (i)=>CSSMachine.gothrough(i));
                return code;
        }
        const mergeBranch = function(code){
                if(!code){return}
                return code.replace(/\$\{(\d+)\}/g, (m,a)=>BRANCH[a]);
        }
        const Rules = {
            STATE_NORMAL: {
                transitions: [
                    {
                    condition: (o) => o.char === '<' && (/[\/\w]/.test(o.next)),
                    toState: 'STATE_TAG',
                    charProcessor: (char)=>`<span class="html-tag">&lt;</span>`,
                    },
                    {
                    condition: (o) => o.char === '<' && o.next==='!',
                    toState: 'STATE_COMMENT',
                    charProcessor: (char)=>`<span class="html-comment">&lt;</span>`,
                    },
                ],
                charProcessor: tagFree,
            },
            STATE_TAG: {
                transitions: [
                    {
                    condition: (o) => (/\s/.test(o.char)),
                    toState: 'STATE_ATTR_NAME',
                    },
                    {
                    condition: (o) => o.char==='>',
                    toState: 'STATE_NORMAL',
                    charProcessor: (char)=>`<span class="html-tag">&gt;</span>`,
                    },
                ],
                entryToken: `<span class="html-tag">`,
                exitToken: `</span>`,
                charProcessor: tagFree,
            },
            STATE_ATTR_NAME: {
                transitions: [
                    {
                    condition: (o) => o.char === '"' || o.char === "'" || o.char=== "`",
                    toState: 'STATE_ATTR_VALUE',
                    charProcessor: (char)=>`<span class="html-tag">${char}</span>`,
                    },
                    {
                    condition: (o) => o.char==='>',
                    toState: 'STATE_NORMAL',
                    charProcessor: (char)=>`<span class="html-tag">&gt;</span>`,
                    },
                ],
                entryToken: `<span class="html-attr-name">`,
                exitToken: `</span>`,
                charProcessor: tagFree,
            },
            STATE_ATTR_VALUE: {
                transitions: [
                    {
                    condition: (o) => o.char===o.pairChar && o.pre!=='\\',
                    toState: 'STATE_TAG',
                    charProcessor: (char)=>`<span class="html-tag">${char}</span>`,
                    },
                ],
                entryToken: `<span class="html-attr-value">`,
                exitToken: `</span>`,
                charProcessor: tagFree,
            },
            STATE_COMMENT: {
                transitions: [
                    {
                    condition: (o) => o.char==='>',
                    toState: 'STATE_NORMAL',
                    charProcessor: (char)=>`<span class="html-comment">&gt;</span>`,
                    },
                ],
                entryToken: `<span class="html-comment">`,
                exitToken: `</span>`,
                charProcessor: tagFree,
            },
        }
        const htmlMachine = this.StateMachine(Rules);
        const HMI = {
            gothrough: (code)=>{
                code = getBranch(code);
                const result = htmlMachine.gothrough(code);
                return mergeBranch(result);
            }
        }
        return HMI;
    }
    
    // Markdown Machine
    markdownMachine = (option) => {
        const tagFree = this.tagFree, trim = this.trim;
        const { highlightCode=false } = option||{};
        const HTMLMachine = this.htmlMachine();
        const ESMachine = this.esMachine();
        const PythonMachine = this.esMachine('python');
        const VBMachine = this.esMachine('vb');
        const highlights = {
            html: HTMLMachine,
            xml: HTMLMachine,
            vue: HTMLMachine,
            css: this.cssMachine(),
            sql: this.sqlMachine(),
            yaml: this.yamlMachine(),
            javascript: ESMachine,
            java: ESMachine,
            json: ESMachine,
            toml: ESMachine,
            jsx: ESMachine,
            typescript: ESMachine,
            coffeescript: ESMachine,
            pseudocode: ESMachine,
            dart: ESMachine,
            livescript: ESMachine,
            go: ESMachine,
            c: ESMachine,
            csharp: ESMachine,
            cpp: ESMachine,
            php: ESMachine,
            python: PythonMachine,
            vbscript: VBMachine,
            asp: VBMachine,
            vb: VBMachine,
        }
        const inlineRules = {
            STATE_NORMAL:{
                transitions: [
                    {
                    condition: (o)=> o.char === '`',
                    toState: 'STATE_CODE',
                    charProcessor: (char)=>'',
                    },
                    {
                    condition: (o)=> o.char === '~' && o.next === '~',
                    toState: 'STATE_DEL',
                    charProcessor: (char)=>'',
                    charStep: 1,
                    },
                    {
                    condition: (o)=> (o.char === '*' && o.next === '*' || o.char === '_' && o.next === '_'),
                    toState: 'STATE_STRONG',
                    charProcessor: (char)=>'',
                    charStep: 1,
                    },
                    {
                    condition: (o)=> (o.char === '*' && o.pre===' ' && o.next!==' ' || o.char === '_' && o.pre === ' ' && o.next!==' '),
                    toState: 'STATE_EM',
                    charProcessor: (char)=>'',
                    },
                ],
                charProcessor: tagFree,
            },
            STATE_CODE:{
                transitions: [
                    {
                    condition: (o)=> o.char==='`' && o.pre!=='`' && o.next!=='`',
                    toState: 'STATE_NORMAL',
                    charProcessor: (char)=>'',
                    }
                ],
                entryToken: `<code>`,
                exitToken: `</code>`,
                charProcessor: (char)=>{return tagFree(char).replace(/(\[)|\]/g, (m,a)=>a?'&#91;':'&#93;');},
            },
            STATE_EM:{
                transitions: [
                    {
                    condition: (o)=> o.char===o.pairChar,
                    toState: 'STATE_NORMAL',
                    charProcessor: (char)=>'',
                    },
                    {
                    condition: (o)=> (o.char === '*' && o.next === '*' || o.char === '_' && o.next === '_'),
                    toState: 'STATE_EM_STRONG',
                    nestState: true,
                    charProcessor: (char)=>'',
                    charStep: 1,
                    },
                    {
                    condition: (o)=> o.char === '`',
                    toState: 'STATE_CODE',
                    nestState: true,
                    charProcessor: (char)=>'',
                    },
                ],
                entryToken: `<em>`,
                exitToken: `</em>`,
                charProcessor: tagFree,
            },
            STATE_STRONG:{
                transitions: [
                    {
                    condition: (o)=> o.char===o.pairChar && o.next===o.pairChar,
                    toState: 'STATE_NORMAL',
                    charProcessor: (char)=>'',
                    charStep: 1,
                    },
                    {
                    condition: (o)=> (o.char === '*' && o.pre===' ' && o.next!==' ' || o.char === '_' && o.pre === ' ' && o.next!==' '),
                    toState: 'STATE_STRONG_EM',
                    nestState: true,
                    charProcessor: (char)=>'',
                    },
                    {
                    condition: (o)=> o.char === '`',
                    toState: 'STATE_CODE',
                    nestState: true,
                    charProcessor: (char)=>'',
                    },
                ],
                entryToken: `<strong>`,
                exitToken: `</strong>`,
                charProcessor: tagFree,
            },
            STATE_EM_STRONG:{
                transitions: [
                    {
                    condition: (o)=> o.char===o.pairChar && o.next===o.pairChar,
                    toState: -1,
                    charProcessor: (char)=>'',
                    charStep: 1,
                    }
                ],
                entryToken: `<em><strong>`,
                exitToken: `</strong></em>`,
                charProcessor: tagFree,
            },
            STATE_STRONG_EM:{
                transitions: [
                    {
                    condition: (o)=> o.char===o.pairChar,
                    toState: -1,
                    charProcessor: (char)=>'',
                    }
                ],
                entryToken: `<strong><em>`,
                exitToken: `</em></strong>`,
                charProcessor: tagFree,
            },
            STATE_DEL:{
                transitions: [
                    {
                    condition: (o)=> o.char===o.pairChar && o.next===o.pairChar,
                    toState: 'STATE_NORMAL',
                    charProcessor: (char)=>'',
                    charStep: 1,
                    }
                ],
                entryToken: `<del>`,
                exitToken: `</del>`,
                charProcessor: tagFree,
            },
        }
        const _inline = {};
        const inlineProcessor = (token, currentState, toState)=>{
            let data = token;
            switch(currentState){
                case 'STATE_CODE_BLOCK':
                    if(/^\s*```$/.test(token)){
                        if(highlightCode){
                            const fnHighlight = highlights[_inline['STATE_CODE_BLOCK']['type']];
                            const inlineToken = _inline['STATE_CODE_BLOCK']['token'];
                            const code = fnHighlight?.gothrough(inlineToken) || tagFree(inlineToken);
                            data = `${code}</pre>`;
                        }else{
                            data = `</pre>`;
                        }
                    }else{
                        if(highlightCode){
                            _inline['STATE_CODE_BLOCK']['token'] += token + '\n';
                            data = '';
                        }else{
                            data = tagFree(token)+'\n';
                        }
                    }
                    break;
                case 'STATE_TABLE':
                    if(toState==='STATE_NORMAL'){
                        const leftToken = inlineProcessor(token, 'STATE_NORMAL');
                        data = `</table><br>${leftToken}`;
                    }else if(/^\|\s*\-+|\-+\s*\|$/.test(token)){
                        data = '';
                    }else if(/^\|\s*(.*?)\s*\|$/.test(token)){
                        let td = RegExp.$1.split(/\s*\|\s*/);
                        td = td.map(item=>mdInline.gothrough(item));
                        data = `<tr><td>${td.join('</td><td>')}</td></tr>`;
                    }else if(/^\|/.test(token)){
                        data = `<tr><td colspan="100">${mdInline.gothrough(token)}</td></tr></table>`;
                    }else{
                        data = `</table><br>${mdInline.gothrough(token)}`;
                    }
                    break;
                default:
                    if(toState==='STATE_CODE_BLOCK'){
                        if(/^\s*```\s*(.*?)$/.test(token)){
                            let type = RegExp.$1 || 'plain text';
                            data = `<pre class="code" data-type="${type}" data-copy="⎘">`;
                            _inline['STATE_CODE_BLOCK']={type, token:''};
                        }
                    }else if(toState==='STATE_TABLE'){
                        if(/^\|\s*(.*?)\s*\|$/.test(token)){
                            let td = RegExp.$1.split(/\s*\|\s*/);
                            td = td.map(item=>mdInline.gothrough(item));
                            data = `<table data-copy="⎘"><tr><th>${td.join('</th><th>')}</th></tr>`;
                        }
                    }else if(/^(\s*)[\+\-\*]\s+(.+)$/.test(token)){
                        let b = RegExp.$1?.length, c = RegExp.$2;
                        let l = (b?b-1:0)*2/2;
                        if(l<0){l=0}
                        let o = (b?b-1:0)%2?'square':'disc';
                        data = `<li style="margin-left:${l}rem;list-style:${o};">${mdInline.gothrough(c)}</li>`
                    }else if(/^(\d+[\.）].+)$/.test(token)){
                        data = `${mdInline.gothrough(RegExp.$1)}`;
                    }else if(/(^\#{1,6})\s+(.+)$/.test(token)){
                        let n = RegExp.$1?.length, t = RegExp.$2;
                        data = `<h${n}>${mdInline.gothrough(t)}</h${n}>`;
                    }else if(/^\>\s+(.+)$/.test(token)){
                        data = `<blockquote>${mdInline.gothrough(RegExp.$1)}</blockquote>`;
                    }else if(/^[\*\-_]{3,}$/.test(token)){
                        data = `<hr noshade size="1px" />`;
                    }else{
                        data = `${mdInline.gothrough(token)}`.replace(/\!\[([^\]]+?)\]\(([^\)]+?)\)/g, '<img src="$2" alt="$1">')
                        .replace(/\[([^\]]+?)\]\(([^\)]+?)\)/g, (a,b,c)=>`<a href="${c.replace(/<em>/ig,'_')}" target="_blank">${b}</a>`);
                    }
            }
            return data;
        }
        const checkBlockState = (token, scope)=>{
            switch(scope){
                case 'STATE_CODE_BLOCK':
                    if(/^\s*```$/.test(token)){
                        return 'STATE_NORMAL';
                    }
                    return 'STATE_CODE_BLOCK';
                    break;
                case 'STATE_TABLE':
                    if(/^\|\s*(.*?)\s*\|$/.test(token)){
                        return 'STATE_TABLE';
                    }
                    return 'STATE_NORMAL';
                    break;
                default:
                    if(/^\s*```\s*(.*?)$/.test(token)){
                        return 'STATE_CODE_BLOCK';
                    }else if(/^\|\s*(.*?)\s*\|$/.test(token)){
                        return 'STATE_TABLE';
                    }else{
                        return 'STATE_NORMAL';
                    }
            }
        }
        const blockRules = {
            STATE_NORMAL: {
                transitions: [
                    {
                    condition: (o) => o.char === '\n',
                    toState: checkBlockState,
                    charProcessor:()=>'<br>',
                    tokenProcessor: inlineProcessor,
                    },
                ],
                tokenProcessor: inlineProcessor,
            },
            STATE_CODE_BLOCK: {
                transitions: [
                    {
                    condition: (o) => o.char === '\n',
                    toState: checkBlockState,
                    charProcessor:()=>'',
                    tokenProcessor: inlineProcessor,
                    },
                ],
                tokenProcessor: inlineProcessor,
            },
            STATE_TABLE: {
                transitions: [
                    {
                    condition: (o) => o.char === '\n',
                    toState: checkBlockState,
                    charProcessor:()=>'',
                    tokenProcessor: inlineProcessor,
                    },
                ],
                tokenProcessor: inlineProcessor,
            }
        }
    
        const mdBlock = this.StateMachine(blockRules);
        const mdInline = this.StateMachine(inlineRules);
        return mdBlock;
    }

    formatMarkdown = (code, typing, highlight) => {
        let mdMachine = window.mdMachine, mdMachineHLight = window.mdMachineHLight;
        let htmlStr;
        if(highlight){
            if(!mdMachineHLight){
                mdMachineHLight = this.markdownMachine({highlightCode:true});
                window.mdMachineHLight = mdMachineHLight;
            }
            htmlStr = mdMachineHLight.gothrough(code);
        }else{
            if(!mdMachine){
                mdMachine = this.markdownMachine({highlightCode:false});
                window.mdMachine = mdMachine;
            }
            htmlStr = mdMachine.gothrough(code);
        }
        if(typing){
            htmlStr = htmlStr.replace(/\n*$/g,'').replace(/(?:<br>)*$/g,'') + `<span class="thinking"></span>`;
        }
        return htmlStr;
    }

    // Network
    request = (options={}) => {
        let { url, method, header, params, payload, onsuccess=()=>{}, onresponse=()=>{}, onerror=()=>{} } = options;
        if(!url){return;}
        let xhr = new XMLHttpRequest();
        if(!method){method = 'GET';}
        if(params && typeof params === 'object'){
            const sparams = [];
            Object.entries(params).map(kv=>{
                sparams.push(kv[0] + '=' + kv[1]);
            });
            if(/\?/.test(url)){
                url += '&' + sparams.join('&');
            }else{
                url += '?' + sparams.join('&');
            }
        }
        xhr.open(method, url, true);
        if(header && typeof header === 'object'){
            Object.entries(header).map(kv=>{
                xhr.setRequestHeader(kv[0], kv[1]);
            });
        }
        xhr.addEventListener('error', (e) =>{
            onerror(e.type);
            xhr = null;
        });
        xhr.onload = () =>{
            xhr = null;
        }
        xhr.send(typeof payload === 'object' ? JSON.stringify(payload) : payload?.toString());
        xhr.onreadystatechange = function () {
            if (xhr.readyState === 4) {
                if(xhr.status === 200){
                    onresponse(xhr.responseText);
                    try{
                        const data = JSON.parse(xhr.responseText);
                        if(data.code !== '200'){
                            onerror(xhr.responseText);
                        }else{
                            onsuccess(data);
                        }
                    }catch(e){
                        onerror('The response text serialized error!');
                    }
                }else{
                    onerror('Request status '+xhr.status);
                }
            }
        }
    }

    initWS = () => {
        const api = this.templateReplace(this.wsAPI, {...this});
        const url = this.wServer + api;
        const onerror = (e) => {
            console.log('WebSocket error: ' + e);
            return e;
        }
        const onmessage = (data) => {
            this.answerTyping(JSON.parse(data));
        }

        return new Promise((resolve, reject) => {

            let socket = new WebSocket(url);

            socket.addEventListener("open", (event) => {
                this.socket = socket;
                resolve(socket);
                console.log("WebSocket 连接已建立");
            });

            // 监听消息接收事件
            socket.addEventListener("message", (event) => {
                onmessage(event.data);
            });
            
            // 监听错误事件
            socket.addEventListener("error", (event) => {
                // console.error("WebSocket 错误: ", event);
                reject(event.type);
            });

            // 监听连接关闭事件
            socket.addEventListener("close", (event) => {
                this.socket = null;
                // const wdDoms = this.chatDom.getElementsByClassName('word');
                // const wdDom = wdDoms[wdDoms.length-1];
                // if(wdDom){
                //     wdDom.innerHTML = this.typingWords;
                // }
                const tpDom = this.chatDom.getElementsByClassName('thinking')[0];
                if(tpDom){
                    tpDom.remove();
                }
                if(this.input){
                    this.input.parentNode.classList.remove('talking');
                }
                this.typingWords = '';
                this.typing = false;
                this.setChatWaiting(false);
                console.log("WebSocket 连接已关闭");
            });

        }).then(
            (ws)=>ws,
            (e)=>{onerror(e);}
        );
    }

    // API
    getChatId = () => {
        const api = this.templateReplace(this.getChatAPI, {...this});
        const url = this.endpoint + api;
        return new Promise((resolve, reject) => {
            this.request({
                url,
                header: {
                    Authorization: this.authorization
                },
                params: {
                    session_id: this.sessionId
                },
                onsuccess: resolve,
                onerror: reject,
            });
        }).then(res=>res.data[0]?.id, (e)=>{
            this.failedMessage = `Kubechat get chat session error:\n${e}`;
            console.log(this.failedMessage);
            return 'error';
        });
    }

    getChatHistory = () => {
        const api = this.templateReplace(this.getHistoryAPI, {...this});
        const url = this.endpoint + api;
        return new Promise((resolve, reject) => {
            this.request({
                url,
                header: {
                    Authorization: this.authorization
                },
                params: {
                    session_id: this.sessionId
                },
                onsuccess: resolve,
                onerror: reject,
            });
        }).then(res=>res.data?.history, (e)=>{
            this.warningMessage = [`Kubechat get chat history error:\n${e}`, ...this.warningMessage];
            console.log(this.warningMessage[0]);
            return 'error';
        });
    }

    newChatId = () => {
        const api = this.templateReplace(this.newChatAPI, {...this});
        const url = this.endpoint + api;
        return new Promise((resolve, reject) => {
            this.request({
                url,
                method: 'POST',
                header: {
                    Authorization: this.authorization
                },
                params: {
                    session_id: this.sessionId
                },
                onsuccess: resolve,
                onerror: reject,
            });
        }).then(res=>res.data?.id, (e)=>{
            this.failedMessage = `Kubechat create new chat session error:\n${e}`;
            console.log(this.failedMessage);
            return 'error';
        });
    }

    newVote = (options={}) => {
        const {messageid, upvote, downvote} = options;
        if(!messageid){return;}
        return new Promise((resolve, reject) => {
            this.request({
                url: this.endpoint + '/api/v1/bots/' + this.botId + '/web-chats/' + this.chatId+ '/messages/' + messageid,
                method: 'POST',
                header: {
                    Authorization: this.authorization
                },
                payload: {
                    'upvote': upvote,
                    'downvote': downvote
                },
                onsuccess: resolve,
                onerror: reject,
            });
        }).then(res=>res.data?.id, (e)=>{
            this.warningMessage = [`Kubechat vote error:\n${e}`, ...this.warningMessage];
            console.log(this.warningMessage[0]);
            return 'error';
        });
    }

    clearHistory = (method) => {
        const api = this.templateReplace(this.clearHistoryAPI, {...this});
        const url = this.endpoint + api;
        if(!method){method = 'PUT'}
        return new Promise((resolve, reject) => {
            this.request({
                url,
                method,
                header: {
                    Authorization: this.authorization
                },
                params: {
                    session_id: this.sessionId
                },
                onsuccess: resolve,
                onerror: reject,
            });
        }).then(res=>res, (e)=>{
            this.warningMessage = [`Kubechat clear chat history error:\n${e}`, ...this.warningMessage];
            console.log(this.warningMessage[0]);
            return 'error';
        });
    }

    // Handle click event
    handleClick = (e) => {
        const dom = e.target, tag = dom.tagName.toLowerCase(), cls = dom.classList;
        // console.log(tag, cls);
        switch(tag){
            case 'input':
                if(dom.id==='upload-image'){
                    //bind upload-image event
                    const upload_image_tool = this.upload_image_tool
                    if(!upload_image_tool){
                        dom.addEventListener('change', (e) => {
                            e.stopImmediatePropagation();
                            const input = e.target;
                            const file = input?.files?.[0];
                            const maxSize = 1024 * 1024 * 20;
                            if(file?.size > maxSize){
                                console.log('File size exceeds 20M.');
                                return
                            }
                            const action_items_container = this.action_items_container || this.bot.getElementsByClassName('action-items')[0];
                            if (file && action_items_container) {
                                this.action_items_container = action_items_container;
                                const reader = new FileReader();
                                reader.onload = function(e) {
                                    const base64 = e.target.result;
                                    const item = document.createElement('div');
                                    item.className = 'action-item';
                                    item.innerHTML = `<img class="action-item" src="${base64}" />`;
                                    action_items_container.appendChild(item);
                                    action_items_container.classList.remove('invisible');

                                };
                                reader.readAsDataURL(file);
                            }
                            input.value = '';
                        });
                        this.upload_image_tool = dom;
                    }
                }
                break;
            case 'span':
                if(cls.contains('close')){
                    this.setBotExpand(false);
                }else if(cls.contains('toggle')){
                    this.toggleFullScreen();
                    dom.innerHTML = this.isFullScreen ? '&swarr;' : '&nearr;';
                }else if(cls.contains('dismiss')){
                    this.showReference(false);
                }else if(cls.contains('speaking')){
                    this.recognition.stop();
                }else if(cls.contains('speech')){
                    this.recognition.go(dom);
                }else if(cls.contains('send')){
                    this.askQuestion();
                }else if(cls.contains('stop')){
                    this.stopAnswer();
                }
                break;
            case 'i':
                if(cls.contains('faq')){
                    this.askQuestion(dom.textContent);
                }
                break;
            case 'button':
                if(cls.contains('like')){
                    const data = { 
                        'messageid': dom.getAttribute('data-id'), 
                        'upvote': cls.contains('voted')?0:1,
                        'downvote': dom.parentNode.getElementsByClassName('dislike voted')[0]?1:0
                    }
                    this.newVote(data);
                    cls.toggle('voted');
                }else if(cls.contains('dislike')){
                    const data = { 
                        'messageid': dom.getAttribute('data-id'), 
                        'downvote': cls.contains('voted')?0:1,
                        'upvote': dom.parentNode.getElementsByClassName('like voted')[0]?1:0
                    }
                    this.newVote(data);
                    cls.toggle('voted');
                }
                break;
            case 'div':
                if(cls.contains('reference')){
                    const ref = dom.getElementsByClassName('ref-detail')[0]?.innerHTML;
                    this.showReference(ref);
                }else if(cls.contains('stop-speak')){
                    cls.replace('stop-speak', 'speaker');
                    this.stopSpeak();
                }else if(cls.contains('speaker')){
                    const answerDom = dom.parentNode.parentNode.getElementsByClassName('word')[0];
                    const answerText = answerDom?.innerText;
                    if(answerText){
                        cls.replace('speaker', 'stop-speak');
                        this.beforeSpeakEvent.message = {
                            "text": answerText
                        };
                        if(!this.dispatchEvent(this.beforeSpeakEvent)){
                            return;
                        }
                        this.speak(answerText, ()=>{cls.replace('stop-speak', 'speaker');});
                    }
                }else if(cls.contains('action-item')){
                    const action_items_container = this.action_items_container;
                    dom.remove()
                    if(action_items_container.getElementsByClassName('action-item').length===0){
                        action_items_container.classList.add('invisible');
                    }
                }
                break;
            case 'pre':
                if(cls.contains('code')){
                    this.copyText(dom);
                    dom.setAttribute('data-copy', '✔︎');
                    setTimeout(()=>{dom.setAttribute('data-copy', '⎘');}, 500);
                }
                break;
            case 'table':
                this.copyText(dom);
                dom.setAttribute('data-copy', '✔︎');
                setTimeout(()=>{dom.setAttribute('data-copy', '⎘');}, 500);
                break;
            default:
                break;
        }
    }

    handleKeyDown = (e) => {
        e.stopPropagation();
        if(!this.waiting && (e.metaKey || e.ctrlKey) && e.keyCode === 13){
            this.askQuestion();
        }
    }

    // Ask question
    askQuestion = async (question) => {
        const input = this.input || this.bot.getElementsByClassName('input')[0];
        if(!input || this.waiting){return;}
        this.input = input;
        const msg = question || input?.value;
        if(!msg || msg.replace(/[\s]/g,'')===''){return;}
        if(this.typing){
            this.stopAnswer();
            return;
        }
        this.setChatWaiting(true);
        input.value = '';
        const instruction = msg.toLowerCase();
        if(instruction==='/clear' || instruction==='/reset'){
            const method = instruction==='/clear' ? 'PUT' : 'DELETE';
            const SpinCls = this.spin.classList;
            SpinCls.add('waiting')
            const result = await this.clearHistory(method);
            if(result.code==='200'){
                this.clearEvent.message = {
                    "session": this.sessionId,
                    "raw": 'done',
                };
                this.dispatchEvent(this.clearEvent);
                if(method==='DELETE'){
                    this.stopAnswer();
                    await this.initEnv();
                }
                this.renderChats([],true);
            }
            SpinCls.remove('waiting');
            if(this.mode!=='offstage'){
                this.sayWelcome();
            }
            this.setChatWaiting(false);
            return;
        }
        const timestap = new Date().getTime();
        const list = [
            {
                "type": "message",
                "role": "human",
                "data": msg,
                "timestamp": timestap
            },
            {
                "type": "thinking",
                "role": "ai",
                "data": "",
                "timestamp": ""
            }
        ];
        let formatMsg = this.sendRawMessage ? msg : JSON.stringify(list[0]);
        const action_items_container = this.action_items_container;
        let messages = [];
        if(action_items_container){
            messages = [{"type": "text", "text": msg}];
            Array.from(action_items_container.getElementsByTagName('img')).map(item=>{
                messages.push({"type": "image_url", "image_url": {"url":item.src}})
            })
            list[0].data = messages;
            formatMsg = JSON.stringify(list[0]);
            action_items_container.innerHTML = '';
            action_items_container.classList.add('invisible');
        }

        if(this.mode!=='offstage'){
            this.renderChats(list);
        }
        
        if(!this.socket){
            await this.initWS();
        }
        if(this.socket){
            this.socket.send(formatMsg);
        }
        this.questionEvent.question = {
            "session": this.sessionId,
            "content": msg
        }
        this.dispatchEvent(this.questionEvent);
    }

    // Sync context
    syncContext = (context) => {
        if(typeof context!=='string' || context.replace(/\s/g,'')===''){return;}
        const msg = JSON.stringify({
            "type": "bot_context",
            "role": "bot",
            "data": context,
            "timestamp": new Date().getTime()
        });
        if(this.socket){
            this.socket.send(msg);
        }
    }

    // Welcome
    sayWelcome = () => {
        const welcome = this.welcomeMessage;
        if(!welcome){return;}
        welcome[0].timestamp = new Date().getTime();
        this.renderChats(welcome);
    }

    // Stop answer
    stopAnswer = ()=> {
        if(this.socket){
            this.socket.close(1000, 'Stoped by user');
        }
        this.setChatWaiting(false);
    }

    // Answer typing
    answerTyping = async (options={}) => {
        const { type, id, data, timestamp } = options;
        if(!type){return;}
        const mode = this.mode;
        const wdDoms = this.chatDom.getElementsByClassName('word');
        const wdDom = wdDoms[wdDoms.length-1];
        switch(type){
            case 'welcome':
                const hello = data.hello;
                const faq = data.faq;
                if(hello==='' && faq.length<1){return}
                this.welcomeEvent.message = {
                    "session": this.sessionId,
                    "raw": hello,
                };
                this.dispatchEvent(this.welcomeEvent);
                if(mode==='offstage'){return}
                const list = [{
                    "type": "welcome",
                    "role": "ai",
                    "data": this.formatMarkdown(hello) + (faq.length>0 ? `<p><i class="faq">${faq.join('</i><i class="faq">')}</i></p>` : ''),
                    "timestamp": timestamp
                }];
                this.welcomeMessage = list;
                if(this.chatDom.childElementCount===0){
                    this.renderChats(list);
                }
                break;
            case 'start':
                this.typingWords = '';
                if(mode==='offstage'){return}
                break;
            case 'error':
                if(this.waiting){
                    this.setChatWaiting(false);
                }
                this.typing = false;
                this.typingWords = data;

                this.errorEvent.message = {
                    "session": this.sessionId,
                    "raw": data,
                };
                this.dispatchEvent(this.errorEvent);

                if(mode==='offstage'){return}
                if(this.input){
                    this.input.parentNode.classList.remove('talking');
                }
                if(!wdDom){return;}
                wdDom.innerHTML = data;
                break;
            case 'message':
                if(this.waiting && this.typingWords){
                    this.setChatWaiting(false);
                    if(this.input){
                        this.input.value = '';
                        this.input.parentNode.classList.add('talking');
                    }
                    this.typing = true;
                }
                this.typingWords += data;
                this.streamEvent.message = {
                    "session": this.sessionId,
                    "raw": data,
                };
                this.dispatchEvent(this.streamEvent);
                if(mode==='offstage'){return}
                if(!wdDom){return;}
                wdDom.innerHTML = this.formatMarkdown(this.typingWords, true, false);
                break;
            case 'stop':
                const typingWords = this.typingWords;
                this.typingWords = '';
                this.typing = false;
                this.messageEvent.message = {
                    "session": this.sessionId,
                    "raw": typingWords,
                };
                this.dispatchEvent(this.messageEvent);
                if(mode==='offstage'){return}
                if(!wdDom){return}
                let extraInfo ='';
                const {urls} = options;
                if(urls && urls.length){
                    extraInfo += `<div class="related"><p class="tips">Resources</p>${urls.map((item,index)=>`<p>${index+1}. <a href="${item}" target="_blank">${item}</a></p>`).join('')}</div>`;
                }
                const { related_question_prompt, related_question } = options;
                let tips = related_question_prompt || 'You can continue to ask me';
                if(related_question && related_question.length){
                    extraInfo += `<div class="related"><p class="tips">${tips}</p><p><i class="faq">${related_question.join('</i><i class="faq">')}</i></p></div>`
                }
                const formatedMessage = this.formatMarkdown(typingWords, false, true);
                wdDom.innerHTML = formatedMessage + extraInfo;

                this.dispatchEvent(this.renderEvent);

                const tpDom = wdDom.getElementsByClassName('thinking')[0];
                if(tpDom){tpDom.remove();}
                const infoDom = wdDom.parentNode.getElementsByClassName('info')[0];
                if(infoDom){
                    const respTime = infoDom.getElementsByClassName('time')[0];
                    if(respTime){
                        respTime.textContent = this.timestampToTime(timestamp);
                    }
                    if(!this.disableReference && data && data.length>0){
                        infoDom.insertAdjacentHTML('beforeend', this.stringifyRef(data));
                    }
                    const speaker = infoDom.getElementsByClassName('speaker')[0];
                    if(speaker && !this.disableSpeech){
                        speaker.classList.remove('invisible');
                    }
                    const actionDom = infoDom.parentNode?.parentNode?.getElementsByClassName('action')[0];
                    if(!this.disableFeedback && actionDom){
                        actionDom.innerHTML = this.stringifyVote(id);
                    }
                }
                if(this.input){
                    this.input.parentNode.classList.remove('talking');
                }
                break;
            default:
                this.typingWords = '';
                this.typing = false;
                break;
        }
        if(mode==='offstage'){return}
        const workspace = this.chatDom.parentNode;
        workspace.scrollTop = workspace.scrollHeight;
    }

    // Render chats
    renderChats = (chats, clear) => {
        if(!chats || !chats.map){return;}
        const chatDom = this.chatDom;
        if(!chatDom){return;}
        if(clear){
            chatDom.innerHTML = '';
            return;
        }
        let list = [];
        chats.map((item)=>{
            list.push(['human','user'].includes(item.role) ? this.getTemplateQ(item.data) : this.getTemplateA(item));
        });
        chatDom.insertAdjacentHTML("beforeend", list.join(''));

        this.dispatchEvent(this.renderEvent);

        const workspace = chatDom.parentNode;
        workspace.scrollTop = workspace.scrollHeight;
    }

    // Reference template
    getTemplateRef = (options={}) => {
        let {index, source, score, text} = options;
        return `
        <div class="bd-wrap">
            <div class="title-wrap">
                <div class="index">${index}.</div>
                <div class="title">${source}</div>
                <div class="score">Score: ${score}</div>
            </div>
            <div class="text">${text}</div>
        </div>
    `}

    // Chat container template
    getTemplateQ = (question) => {
        const data = question;
        const images = [];
        if(typeof data !=='string' && data.length>0){
            data.map(item=>{
                if(item.type === 'text'){
                    question = item.text
                }else if(item.type === 'image_url'){
                    images.push(`<img class="action-item" src="${item.image_url?.url}" />`)
                }
            })
        }
        const image_items = images.length>0 ? images.join('')  : '';
        return `
        <div class="topic question">
            <div class="avatar"><div></div></div>
            <div class="content">
                <div class="word">
                    ${question.replace(/\&/g,'&amp;').replace(/(\<)|\>/g, (a,b)=>b?'&lt;':'&gt;')}
                </div>
                <div class="info">
                    ${image_items}
                </div>
            </div>
            <div class="action">
            </div>
        </div>
    `}

    stringifyRef = (refs) => {
        let ref = '';
        let tagFree = this.tagFree;
        if(refs && refs.length>0){
            let refDetail = [];
            refs.map((item, index)=>{
                let data = { 
                    'index': index+1,
                    'score': item.score, 
                    'text': tagFree(item.text),
                    'source': item.metadata?.source,
                }
                refDetail.push(this.getTemplateRef(data));
            });
            ref = `<div class="reference" title="Read ${refs.length} references">${refs.length}<div class="ref-detail">${refDetail.join('')}</div></div>`;
        }
        return ref;
    }

    stringifyVote = (id, upvote, downvote) => {
        return `
            <button class="${upvote?'like voted':'like'}" data-id="${id}"></button>
            <button class="${downvote?'dislike voted':'dislike'}" data-id="${id}"></button>
        `;
    }

    getTemplateA = (options={}) => {
        let { type, id, data, timestamp, references, ref='', urls, url='', upvote, downvote } = options;
        if(type === 'thinking'){
            data = '<div class="thinking"><i></i><i></i><i></i><i></i><i></i></div>';
        }
        if(!this.disableReference && references && references.length>0){
            ref = this.stringifyRef(references);
        }
        if(urls && urls.length){
            url = `<div class="related"><p class="tips">Resources</p>${urls.map((item,index)=>`<p>${index+1}. <a href="${item}" target="_blank">${item}</a></p>`).join('')}</div>`;
        }
        return `
            <div class="topic answer">
                <div class="avatar"><div></div></div>
                <div class="content">
                    <div class="word">
                        ${['thinking','welcome'].includes(type) ? data : this.formatMarkdown(data, false, true) + url}
                    </div>
                    <div class="info">
                        <div class="time">${this.timestampToTime(timestamp)}</div>
                        ${ref}
                        <div class="${!this.disableSpeech && timestamp?'speaker':'speaker invisible'}" title="Voice Listening"></div>
                    </div>
                </div>
                <div class="action">
                    ${!this.disableFeedback && type!=='welcome' ? this.stringifyVote(id, upvote, downvote) : ''}
                </div>
            </div>
        `;
    }

    getTemplate = () => `
    <div class="workspace">
        <div class="hd">
            <h1 class="title">${this.caption}</h1>
            <div class="action">
                <span class="toggle" title="Toggle fullscreen">&nearr;</span>
                <span class="close" title="Close chat">&times;</span>
            </div>
        </div>
        <div class="bd chat">
        </div>
        <div class="ft">
            <div class="container">
                <div class="tool">
                    <span class="${this.disableSpeech?'invisible':'speech'}">
                        <svg viewBox="0 0 1024 1024" version="1.1" xmlns="http://www.w3.org/2000/svg"><path d="M841.142857 402.285714v73.142857c0 169.142857-128 308.553143-292.571428 326.838858V877.714286h146.285714c20.004571 0 36.571429 16.566857 36.571428 36.571428s-16.566857 36.571429-36.571428 36.571429H329.142857c-20.004571 0-36.571429-16.566857-36.571428-36.571429s16.566857-36.571429 36.571428-36.571428h146.285714v-75.446857c-164.571429-18.285714-292.571429-157.696-292.571428-326.838858v-73.142857c0-20.004571 16.566857-36.571429 36.571428-36.571428s36.571429 16.566857 36.571429 36.571428v73.142857c0 141.129143 114.870857 256 256 256s256-114.870857 256-256v-73.142857c0-20.004571 16.566857-36.571429 36.571429-36.571428s36.571429 16.566857 36.571428 36.571428z m-146.285714-219.428571v292.571428c0 100.571429-82.285714 182.857143-182.857143 182.857143s-182.857143-82.285714-182.857143-182.857143V182.857143c0-100.571429 82.285714-182.857143 182.857143-182.857143s182.857143 82.285714 182.857143 182.857143z" fill="currentColor"></path></svg>
                    </span>
                    <span class="${this.disableUploadImage?'invisible':'upload-image'}">
                        <input type="file" id="upload-image" accept=".jpeg,.jpg,.gif,.png,.webp" style="display: none;" />
                        <label for="upload-image">
                            <svg viewBox="0 0 1024 1024" version="1.1" xmlns="http://www.w3.org/2000/svg"><path d="m986.112,211.64474l-75.776,0l0,75.776c0,20.48 -17.408,37.888 -37.888,37.888s-37.888,-17.408 -37.888,-37.888l0,-75.776l-75.776,0c-20.48,0 -37.888,-17.408 -37.888,-37.888s17.408,-37.888 37.888,-37.888l75.776,0l0,-75.776c0,-20.48 17.408,-37.888 37.888,-37.888s37.888,17.408 37.888,37.888l0,75.776l75.776,0c20.48,0 37.888,17.408 37.888,37.888c0,21.504 -17.408,37.888 -37.888,37.888zm-227.328,133.12c0,31.744 -25.6,57.344 -57.344,57.344c-31.744,0 -57.344,-25.6 -57.344,-57.344c0,-31.744 25.6,-57.344 57.344,-57.344s57.344,25.6 57.344,57.344zm-151.552,-133.12l-531.456,0l0,528.384s82.944,-371.712 225.28,-371.712c93.184,0 188.416,287.744 247.808,374.784c0,0 46.08,-188.416 126.976,-189.44c79.872,-1.024 120.832,187.392 120.832,187.392l37.888,0l0,-225.28c0,-20.48 17.408,-37.888 37.888,-37.888s37.888,17.408 37.888,37.888l0,303.104c0,41.984 -33.792,75.776 -75.776,75.776l-758.784,0c-41.984,0 -75.776,-33.792 -75.776,-75.776l0,-607.232c0,-41.984 33.792,-75.776 75.776,-75.776l531.456,0c20.48,0 37.888,17.408 37.888,37.888c0,21.504 -17.408,37.888 -37.888,37.888zm0,0" fill="currentColor" /></svg>
                        </label>
                    </span>
                    <span class="send">
                        <svg viewBox="0 0 1024 1024" version="1.1" xmlns="http://www.w3.org/2000/svg"><path d="m171.27688,292.12551l84.19323,181.66175a90.83087,90.83087 0 0 1 0,76.40274l-84.19323,181.66174a90.97061,90.97061 0 0 0 123.28544,119.54741l516.23377,-257.92474a91.07542,91.07542 0 0 0 0,-162.93662l-516.23377,-257.92474a90.97061,90.97061 0 0 0 -123.32037,119.51247l0.03494,0z" fill="currentColor" /></svg>
                    </span>
                    <span class="stop">
                        <svg viewBox="0 0 1024 1024" version="1.1" xmlns="http://www.w3.org/2000/svg"><path d="m512.00001,901.33389c-102.64257,0 -201.74574,-42.47279 -276.07311,-113.26076c-70.78798,-74.32738 -113.26076,-173.43055 -113.26076,-276.07311c0,-102.64257 42.47279,-201.74574 113.26076,-276.07311c74.32738,-70.78798 173.43055,-113.26076 276.07311,-113.26076c102.64257,0 201.74574,42.47279 276.07311,113.26076c70.78798,74.32738 113.26076,173.43055 113.26076,276.07311c0,102.64257 -42.47279,201.74574 -113.26076,276.07311c-74.32738,70.78798 -173.43055,113.26076 -276.07311,113.26076zm-123.87896,-530.90983c-10.6182,0 -17.697,7.0788 -17.697,17.697l0,247.75792c0,10.6182 7.0788,17.697 17.697,17.697l247.75792,0c10.6182,0 17.697,-7.0788 17.697,-17.697l0,-247.75792c0,-10.6182 -7.0788,-17.697 -17.697,-17.697l-247.75792,0z" fill="currentColor" /></svg>
                    </span>
                </div>
                <label class="ask">
                    <input type="text" class="input" required="required" title="" />
                </label>
                <div class="action-items invisible">
                </div>
            </div>
        </div>
        <div class="ext">
            <div class="hd">
                <h2 class="title">Reference</h2>
                <div class="action">
                    <span class="dismiss" title="Close chat">&times;</span>
                </div>
            </div>
            <div class="bd ext-bd">
            </div>
        </div>
    </div>
    `;

    // Init env
    initEnv = async() => {
        let chatId = await this.getChatId();
        const SpinCls = this.spin.classList;
        if(chatId==='error'){
            this.readyToGo = false;
            SpinCls.add('warning');
            this.spin.title = this.failedMessage;
            this.dispatchEvent(this.failedEvent);
            return;
        }

        if(!chatId){
            chatId = await this.newChatId();
        }
        
        if(!chatId || chatId==='error'){
            this.readyToGo = false;
            SpinCls.add('warning');
            this.spin.title = this.failedMessage;
            this.dispatchEvent(this.failedEvent);
            return;
        }

        this.chatId = chatId;

        let chatHistory = await this.getChatHistory();

        if(typeof chatHistory === 'object'){
            this.renderChats(chatHistory);
        }

        await this.initWS();
        this.readyToGo = true;
        SpinCls.remove('waiting');
        this.dispatchEvent(this.readyEvent);
    }

    showTips = () => {
        const askDom = this.bot.getElementsByClassName('ask')[0];
        if(!askDom){return;}
        let idx = 0, tips = ['tips1', 'tips2', 'tips3'];
        if(!this.disableUploadImage){
            tips.push('tips-vision');
        }
        let len = tips.length;
        setInterval(()=>{
            askDom.classList.remove(tips[idx]);
            if(idx+1>=len){idx=0;}else{idx += 1;}
            askDom.classList.add(tips[idx]);
        },5000);
    }

    connectedCallback() {
        // Create a shadow root
        const shadow = this.attachShadow({ mode: "open" });

        // Check API endpoint and websocket server
        this.endpoint = this.getAttribute("endpoint") || 'https://chat.kubeblocks.io';
        this.wServer = this.getAttribute("wserver") || 'wss://chat.kubeblocks.io';
        this.wsAPI = this.getAttribute("wsapi") || '/api/v1/bots/${botId}/web-chats/${chatId}/connect';
        this.getChatAPI = this.getAttribute("getchatapi") || '/api/v1/bots/${botId}/web-chats';
        this.newChatAPI = this.getAttribute("newchatapi") || '/api/v1/bots/${botId}/web-chats';
        this.getHistoryAPI = this.getAttribute("gethistoryapi") || '/api/v1/bots/${botId}/web-chats/${chatId}';
        this.clearHistoryAPI = this.getAttribute("clearhistoryapi") || '/api/v1/bots/${botId}/web-chats/${chatId}';
        // Check bot mode
        this.mode = this.getAttribute("mode");
        this.sendRawMessage = this.getAttribute("sendrawmessage");
        // Check customized style
        this.customStyle = this.getAttribute("customstyle")||'';

        // Check bot id and integration id
        const botid = this.getAttribute("botid");
        if(!botid){
            const tips = document.createElement('p');
            tips.innerText = '🛠';
            tips.title = 'Need botId';
            shadow.appendChild(tips);
            return;
        }
        this.botId = botid;

        // Check caption
        let caption = this.getAttribute('caption');
        if(caption && caption.replace(/\s/g,'')!==''){
            this.caption = caption;
        }

        // Check sessionid
        let session = this.getAttribute("sessionid");
        if(!session){
            session = this.getCookie('kubechat-session') || Math.random().toString(16).substr(2);
        }
        this.setCookie('kubechat-session', session);
        this.sessionId = session;
        let authorization = this.getAttribute("authorization");
        this.authorization = authorization;

        // Check reference config
        this.disableReference = this.getAttribute("disablereference");
        if(this.disableReference === 'false'){
            this.disableReference = false
        }

        // Check feedback config
        this.disableFeedback = this.getAttribute("disablefeedback");
        if(this.disableFeedback === 'false'){
            this.disableFeedback = false
        }

        // Check speech config
        this.disableSpeech = this.getAttribute("disablespeech");
        if(this.disableSpeech === 'false'){
            this.disableSpeech = false
        }

        // Check upload image config
        this.disableUploadImage = this.getAttribute("disableuploadimage");
        if(this.disableUploadImage === 'false'){
            this.disableUploadImage = false
        }
    
        // Create elements
        const wrapper = document.createElement("div");
        const wrappercls = this.mode ? `wrapper ${this.mode}` : 'wrapper';
        wrapper.setAttribute("class", wrappercls);
    
        const icon = document.createElement("div");
        icon.setAttribute("class", "icon");
    
        // bot
        const bot = document.createElement("div");
        this.bot = bot;
        bot.setAttribute("class", "bot");
        
        bot.innerHTML = this.getTemplate();
        bot.addEventListener('click', this.handleClick);
        bot.addEventListener('keydown', this.handleKeyDown);

        this.chatDom = bot.getElementsByClassName('chat')[0];
        this.refDom = bot.getElementsByClassName('ext')[0];
    
        // Insert icon
        const imgUrl = this.getAttribute("logo");
        const logoCls = imgUrl?"logo customized visible":"logo visible";
        const logo = document.createElement("img");
        this.logo = logo;
        if(imgUrl){
            this.logoIcon = imgUrl;
        }
        logo.src = this.logoIcon;
        logo.setAttribute("class", logoCls);
        logo.setAttribute("tabindex", 0);
        logo.addEventListener('error',()=>{
            logo.src = this.defaultLogo;
            logo.className = 'logo visible';
        })
        logo.addEventListener('click', ()=>{
            this.setBotExpand(!this.botExpand);
        });
        icon.appendChild(logo);

        const likeIcon = this.getAttribute("likeicon");
        if(likeIcon){this.likeIcon = likeIcon}

        const dislikeIcon = this.getAttribute("dislikeIcon");
        if(dislikeIcon){this.dislikeIcon = dislikeIcon}

        // Check human avatar
        const avatar = this.getAttribute('avatar');
        this.avatar = avatar||'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg"><text x="50%" y="60%" dominant-baseline="central" text-anchor="middle" font-size="32">👤</text></svg>';
    
        // Create some CSS to apply to the shadow dom
        const style = document.createElement("style");
        style.textContent = this.getDefaultStyle();

        // Set loading spin
        if(this.mode === 'adaptive'){
            this.spin = bot;
        }else{
            this.spin = icon;
        }
        this.spin.classList.add('waiting');
    
        // Attach the created elements to the shadow dom
        shadow.appendChild(style);
        shadow.appendChild(wrapper);
        wrapper.appendChild(icon);
        wrapper.appendChild(bot);

        // init speech
        if('webkitSpeechRecognition' in window){
            this.bot.classList.add('speech');
            this.recognition = this.initSpeechRecognition();
        }

        // init position
        this.updateBotPosition();

        // Show tips
        this.showTips();

        // Init env
        this.initEnv();

        // // Put it to Agent list
        kubechatComponent.agent.put(botid, this);
    }
    static agent = (function(){
        const Agents = {}
        const AgentAlias = {};
        class Avatar {
            constructor(environment){
                this.environment = environment||{};
            }
            bindAction(actions){
                if(!actions || typeof actions !== 'object'){return}
                Object.keys(actions)?.forEach(methodName => {
                    this[methodName] = actions[methodName].bind(this);
                });
            }
            connectAgent(alias, agentID){
                if(!AgentAlias[alias] && Agents[agentID]){
                    AgentAlias[alias] = agentID;
                }
            }
            getAgent = function(alias){
                return Agents[AgentAlias[alias]];
            }
        }
        const Agent = function(){}
        Agent.prototype.gen = function (options) {
            const { botid, container } = options || {};
            if(Agents[botid] || !container){return}//one botid,one Agent
            const Avatar = document.createElement('kube-chat');
            Object.entries(options).map(item=>{
                Avatar.setAttribute(item[0], item[1]);
            })
            container.appendChild(Avatar);
            Agents[botid] = Avatar;
            return Avatar;
        }
        Agent.prototype.get = function(copilotID){
            return Agents[copilotID];
        }
        Agent.prototype.put = function(copilotID, avatar){
            if(!Agents[copilotID]){
                Agents[copilotID] = avatar;
            }
        }
        Agent.prototype.Avatar = Avatar;
        return new Agent();
    }())
    static mount = (options={}) => {
        const { Element='kube-chat' } = options;
        if (window?.customElements && !window.customElements.get(Element)){
            window.customElements.define(Element, kubechatComponent);
        }
    }
}

export default kubechatComponent;