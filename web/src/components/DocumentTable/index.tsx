import LabelEdit from '@/pages/Collections/documents/labelEdit';
import _ from 'lodash';
import moment from 'moment';
import byteSize from 'byte-size';
import { useEffect, useState } from 'react';
import { useParams,useIntl } from '@umijs/max';
import { Drawer } from 'antd';

function Documentlist({ list, getDocuments, onDelete, loading, selection, editable }) {
  const intl = useIntl();
  const [isSettingShow, setSettingShow] = useState(false);
  const [curItem, setCurItem] = useState({});
  const [tableList, setTableList] = useState([]);
  const [allSelected, setAllSelected] = useState(false);
  const [selectedItems, setSelectedItems] = useState(0);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [sensitiveInfo, setSensitiveInfo] = useState('');
  
  const { collectionId } = useParams();

  const openSettingModal = (item) => {
    setSettingShow(true);
    setCurItem(item);
  };

  const onUpdateSuccess = () => {
    setSettingShow(false);
    getDocuments();
  };

  const selectAll = (e) => {
    let selected = e.target.checked;
    let selections = document.getElementsByName('row-selection');
    setAllSelected(selected);
    setSelectedItems(selected?selections.length:0);
    selections.forEach((item)=>{
      item.checked = selected;
    });
  };

  const selectSingle = (e,idx) => {
    if(!editable || !_.isNumber(idx)){return;}
    let selectionAll = document.getElementsByName('row-selection-all')[0];
    let selections = document.getElementsByName('row-selection');   
    let checkbox = selections[idx];
    let selected = checkbox.checked;
    if(e.target.tagName.toLowerCase()!=='input'){
      selected = !selected;
      checkbox.checked = selected;
    }
    let count = selected ? selectedItems+1 : selectedItems-1;
    selectionAll.indeterminate = false;
    if(count >= selections.length){
      count = selections.length;
      setAllSelected(true);
    }else if(count > 0){
      selectionAll.indeterminate = true;
    }else{
      setAllSelected(false);
    }
    setSelectedItems(count);
  };

  const deleteAll = () =>{
    if(!editable || selectedItems<=0){return;}
    let selections = document.getElementsByName('row-selection');
    let items = [];
    selections.forEach((item)=>{
      if(item.checked){
        items.push(tableList[item.value]);
      }
    });
    onDelete(items);
  };

  const showDrawer = (item) => {
    if(!item || !item.sensitive_info){return;}
    let msg = [`<div class='doc'>🗂 ${item.name}</div>`];
    item.sensitive_info.map((info)=>{
      let chunk = info.chunk, masked_chunk = info.masked_chunk, rules = info.sensitive_info;
      let types = [], cache = {};
      rules.map((rule)=>{
        if(!cache[rule.info_type]){
          cache[rule.info_type] = 1;
        }else{
          cache[rule.info_type] += 1;
        }
        chunk = chunk.replaceAll(rule.text, `<mark>${rule.text}</mark>`);
        masked_chunk = masked_chunk.replaceAll(rule.mask_text, `<mark>${rule.mask_text}</mark>`);
      });
      Object.entries(cache).forEach(([key, value]) => {
        types.push(`
          <em>${key}<sup>${value}</sup></em>
        `);
      });
      
      msg.push(`
      <details class="sensitive-info">
        <summary>
          <div class='title'>
            ${types.join('')}
          </div>
        </summary>
        <p class='chunk'>${chunk}</p>
        <p class='masked-chunk'>${masked_chunk}</p>
      </details>
      `);
      types = null, cache = null;
    });
    setSensitiveInfo(msg.join(''));
    setDrawerOpen(true);
    msg = null;
  };

  const onDrawerClose = () => {
    setDrawerOpen(false);
  };

  useEffect(() => {
    let allStatusReady = true;
    if (list) {
      const newList = _.cloneDeep(list);
      newList.forEach((item) => {
        item.modal = false;
        
        if(item.status?.match(/(?:RUNNING|PENDING)/i)){
          allStatusReady = false;
        }
      });
      setTableList(newList);
      setAllSelected(false);
      setSelectedItems(0);
      const selectionAll = document.getElementsByName('row-selection-all')[0];
      if(selectionAll){
        selectionAll.indeterminate = false;
      }
    }

    const timer = setTimeout(()=>{
      if(allStatusReady){return;}
      getDocuments();
    }, 2000);

    return () => {  
      clearTimeout(timer);  
    };
  }, [list]);

  return (
    <>
      <LabelEdit
        cancel={() => setSettingShow(false)}
        show={isSettingShow}
        onSuccess={onUpdateSuccess}
        collectionId={collectionId}
        document={curItem}
        disabled={curItem?.system}
      />
      <Drawer
        title={intl.formatMessage({ id: 'text.sensitive_info' })}
        placement="right"
        onClose={onDrawerClose} 
        open={drawerOpen}>
        <div dangerouslySetInnerHTML={{ __html: sensitiveInfo }}></div>
      </Drawer>
      <div className={`data-list table document-table ${loading?'waiting':''} ${editable?'':'readonly'}`}>
        <ul>
          <li className="header">
              { selection ? (
              <div className="cell selection">
                <input type="checkbox" name='row-selection-all' checked={allSelected} onChange={selectAll} />
                <a className='action-wrap'>
                  <i className="action-icon">&#9660;</i>
                  <div className="operate-modal">
                    <div
                      className="delete-wrap"
                      onClick={deleteAll}
                    >
                      <i className="delete-icon"></i>
                      <span>
                        {intl.formatMessage({ id: 'action.delete' })}
                      </span>
                    </div>
                  </div>
                </a>
              </div>
              ):''}
              <div className="cell title">
                {intl.formatMessage({ id: 'text.document.name' })}
              </div>
              <div className="cell">
                {intl.formatMessage({ id: 'text.document.type' })}
              </div>
              <div className="cell">
                {intl.formatMessage({ id: 'text.document.size' })}
              </div>
              <div className="cell status">
                {intl.formatMessage({ id: 'text.document.status' })}
              </div>
              <div className="cell">
                {intl.formatMessage({ id: 'text.document.updatedAt' })}
              </div>
              {editable && (
              <div className="cell operation">
                {intl.formatMessage({ id: 'text.document.actions' })}
              </div>
              )}
          </li>
          <li className='column'>
              {selection && (
              <div className="cell selection"></div>
              )}
              <div className="cell title"></div>
              <div className="cell"></div>
              <div className="cell"></div>
              <div className="cell"></div>
              <div className="cell"></div>
              {editable && (
              <div className="cell"></div>
              )}
          </li>
          {tableList &&
            tableList.map((item:any, index) => {
              return (
                <li key={item.id} className='row' onClick={(e)=>{selectSingle(e,index)}}>
                    { selection ? (
                      <div className="cell selection">
                        <input type="checkbox" name='row-selection' value={index} onChange={(e)=>{selectSingle(e,index)}}/>
                      </div>
                    ):''}
                    <div className="cell title">
                      <h5>{item.name}</h5>
                    </div>
                    <div className="cell describe">
                      {item.name
                      .split('.').pop()
                      .toUpperCase()}
                    </div>
                    <div className="cell describe">{byteSize(item.size || 0).toString()}</div>
                    <div className="cell status">
                      <label className={`label-status ${item.status}`}>{item.status}</label>
                    </div>
                    <div className="cell time">
                      {moment(item.updated).fromNow()}
                    </div>
                    {editable && (
                    <div className="cell operation">
                      <a className='operation-wrap'>
                        <i className="more-icon"></i>
                        <div className="operate-modal">
                          { item.sensitive_info?.length>0 ? (
                            <div
                              className="setting-wrap"
                              onClick={(e) => {showDrawer(item);e.stopPropagation();}}
                            >
                              <i className="setting-icon"></i>
                              <span>
                                {intl.formatMessage({ id: 'text.sensitive_info' })}
                              </span>
                            </div>
                          ) : null }
                          <div
                            className="setting-wrap"
                            onClick={(e) => {openSettingModal(item);e.stopPropagation();}}
                          >
                            <i className="setting-icon"></i>
                            <span>
                              {intl.formatMessage({ id: 'text.setting' })}
                            </span>
                          </div>
                          <div
                            className="delete-wrap"
                            onClick={(e) => {onDelete(item);e.stopPropagation();}}
                          >
                            <i className="delete-icon"></i>
                            <span>
                              {intl.formatMessage({ id: 'action.delete' })}
                            </span>
                          </div>
                        </div>
                      </a>
                    </div>
                    )}
                </li>
              );
            })}
        </ul>
      </div>
    </>
  );
}

export default Documentlist;
