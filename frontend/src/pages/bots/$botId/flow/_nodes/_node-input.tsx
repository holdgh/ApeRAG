import { Input, InputProps } from 'antd';
import { TextAreaProps } from 'antd/es/input';
import { useEffect, useRef, useState } from 'react';

export const NodeInput = (props: InputProps) => {
  const [value, setValue] = useState(props.value || props.defaultValue);
  const ref = useRef(null);

  useEffect(() => {
    setValue(props.value || props.defaultValue);
  }, [props.value]);

  return (
    <Input
      {...props}
      value={value}
      ref={ref}
      style={
        props.disabled
          ? {
              borderColor: 'transparent',
            }
          : undefined
      }
      onChange={(e) => {
        setValue(e.currentTarget.value);
      }}
      onBlur={props.onChange}
    />
  );
};

export const NodeInputTextArea = (props: TextAreaProps) => {
  const [value, setValue] = useState(props.value || props.defaultValue);

  useEffect(() => {
    setValue(props.value || props.defaultValue);
  }, [props.value]);

  return (
    <Input.TextArea
      {...props}
      value={value}
      style={
        props.disabled
          ? {
              borderColor: 'transparent',
            }
          : undefined
      }
      onChange={(e) => {
        setValue(e.currentTarget.value);
      }}
      onBlur={props.onChange}
    />
  );
};
