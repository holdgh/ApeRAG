import { FormattedMessage, history } from '@umijs/max';
// import './index.less';

interface IGuideprops {
  btn: string;
  text: string;
  path: string;
  classname: string;
}

const Guide = (props: IGuideprops) => {
  const { text, classname, btn, path } = props;

  const handleClick = () => {
    history.push(path);
  };

  return (
    <div className="guide-box">
      <div className={classname}></div>
      <div className="guide-text">
        <FormattedMessage id={text} />
        <br />
        <FormattedMessage id="bots.guide.desc" />
      </div>

      <div className="button-wrap">
        <button type="button" onClick={handleClick}>
          <FormattedMessage id={btn} />
        </button>
      </div>
    </div>
  );
};

export default Guide;
