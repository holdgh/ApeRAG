import { MODEL_PROVIDER_ICON } from '@/constants';
import { getProviderByModelName } from '@/utils';
import { Avatar, Select, SelectProps, Space, theme, Typography } from 'antd';
import _ from 'lodash';
import { useMemo } from 'react';
import { UndrawEmpty } from 'react-undraw-illustrations';
import { FormattedMessage, useModel } from 'umi';

type ModelSelectProps = {
  model: 'embedding' | 'completion' | 'rerank';
};

export const ModelSelect = (props: SelectProps & ModelSelectProps) => {
  const { token } = theme.useToken();
  const { availableModels } = useModel('models');

  const modelOptions = useMemo(
    () =>
      _.map(availableModels, (provider) => {
        return {
          label: (
            <Space>
              <Avatar
                size={24}
                shape="square"
                src={
                  provider.name ? MODEL_PROVIDER_ICON[provider.name] : undefined
                }
              />
              <span>{provider.label || provider.name}</span>
            </Space>
          ),
          options: provider[props.model]?.map((item) => {
            return {
              label: item.model,
              value: item.model,
            };
          }),
        };
      }).filter((item) => !_.isEmpty(item.options)),
    [availableModels, props.model],
  );

  const { provider } = getProviderByModelName(
    props.value,
    props.model,
    availableModels,
  );

  return (
    <Select
      {...props}
      options={modelOptions}
      suffixIcon={null}
      labelRender={({ label, value }) => {
        return (
          <Space style={{ alignItems: 'center' }}>
            {provider?.name && (
              <Avatar
                size={24}
                shape="square"
                src={MODEL_PROVIDER_ICON[provider.name]}
                style={{
                  transform: 'translateY(-1px)',
                }}
              />
            )}
            {label || value}
          </Space>
        );
      }}
      notFoundContent={
        <Space
          direction="vertical"
          style={{
            display: 'flex',
            alignItems: 'center',
            marginBlock: 24,
          }}
        >
          <UndrawEmpty primaryColor={token.colorPrimary} height="80px" />
          <Typography.Text type="secondary">
            <FormattedMessage id="collection.model_not_found" />
          </Typography.Text>
        </Space>
      }
    />
  );
};
