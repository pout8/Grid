/**
 * 价格格式化工具函数
 * 根据价格大小自动调整显示精度
 */

/**
 * 格式化价格显示
 * @param price 价格数值
 * @param minDecimals 最小小数位数，默认2
 * @param maxDecimals 最大小数位数，默认8
 * @returns 格式化后的价格字符串
 */
export const formatPrice = (
  price: number | string | undefined,
  minDecimals: number = 2,
  maxDecimals: number = 8
): string => {
  if (price === undefined || price === null || price === '') {
    return '0.00';
  }

  const numPrice = typeof price === 'string' ? parseFloat(price) : price;

  if (isNaN(numPrice)) {
    return '0.00';
  }

  // 根据价格大小动态调整精度
  let decimals: number;

  if (numPrice >= 1000) {
    // 大于1000，显示2位小数
    decimals = 2;
  } else if (numPrice >= 1) {
    // 1-1000之间，显示2-4位小数
    decimals = 4;
  } else if (numPrice >= 0.01) {
    // 0.01-1之间，显示4位小数
    decimals = 4;
  } else if (numPrice >= 0.0001) {
    // 0.0001-0.01之间，显示6位小数
    decimals = 6;
  } else {
    // 小于0.0001，显示8位小数
    decimals = 8;
  }

  // 确保在min和max范围内
  decimals = Math.max(minDecimals, Math.min(decimals, maxDecimals));

  return numPrice.toFixed(decimals);
};

/**
 * 格式化价格显示（带货币符号）
 * @param price 价格数值
 * @param currency 货币符号，默认'$'
 * @param minDecimals 最小小数位数
 * @param maxDecimals 最大小数位数
 * @returns 格式化后的价格字符串
 */
export const formatPriceWithSymbol = (
  price: number | string | undefined,
  currency: string = '$',
  minDecimals?: number,
  maxDecimals?: number
): string => {
  return `${currency}${formatPrice(price, minDecimals, maxDecimals)}`;
};

/**
 * 格式化金额（添加千位分隔符）
 * @param amount 金额数值
 * @param decimals 小数位数，默认2
 * @returns 格式化后的金额字符串
 */
export const formatAmount = (
  amount: number | string | undefined,
  decimals: number = 2
): string => {
  if (amount === undefined || amount === null || amount === '') {
    return '0.00';
  }

  const numAmount = typeof amount === 'string' ? parseFloat(amount) : amount;

  if (isNaN(numAmount)) {
    return '0.00';
  }

  return numAmount.toLocaleString('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
};