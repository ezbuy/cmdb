function cronValidate(frequency) {
    let cron = frequency;
    let result = CronExpressionValidator.validateCronExpression(cron);
    console.log(result);
    if (result == true) {
        console.log("频率格式正确");
    }
    else {
        alert("频率格式错误");
    }
    return result;
}

function CronExpressionValidator() {
}

CronExpressionValidator.validateCronExpression = function (value) {
    if (value == null || value.length == 0) {
        return false;
    }

    // split and test length
    let expressionArray = value.split(" ");
    let len = expressionArray.length;

    if ((len != 5 && (len != 6))) {
        return false;
    }

    // check only one question mark
    let match = value.match(/\?/g);
    if (match != null && match.length > 1) {
        return false;
    }

    // check only one question mark
    let dayOfTheMonthWildcard = "";

    // if appropriate length test parts
    // [0] Seconds 0-59 , - * /
    if (CronExpressionValidator.isNotWildCard(expressionArray[0], /[\*]/gi)) {
        if (!CronExpressionValidator.segmentValidator("([0-9\\\\,-\\/])", expressionArray[0], [0, 59], "minutes")) {
            return false;
        }
    }

    // [1] Hours 0-23 , - * /
    if (CronExpressionValidator.isNotWildCard(expressionArray[1], /[\*]/gi)) {
        if (!CronExpressionValidator.segmentValidator("([0-9\\\\,-\\/])", expressionArray[1], [0, 23], "hours")) {
            return false;
        }
    }

    // [2]  Day of month 1-31 , - * ? / L W C
    if (CronExpressionValidator.isNotWildCard(expressionArray[2], /[\*]/gi)) {
        if (!CronExpressionValidator.segmentValidator("([0-9LWC\\\\,-\\/])", expressionArray[2], [1, 31], "days of the month")) {
            return false;
        }
    } else {
        dayOfTheMonthWildcard = expressionArray[3];
    }

    // [3] Month 1-12 or JAN-DEC , - * /
    if (CronExpressionValidator.isNotWildCard(expressionArray[3], /[\*]/gi)) {
        expressionArray[3] = CronExpressionValidator.convertMonthsToInteger(expressionArray[3]);
        if (!CronExpressionValidator.segmentValidator("([0-9\\\\,-\\/])", expressionArray[3], [1, 12], "months")) {
            return false;
        }
    }

    // [4] Day of week 1-7 or SUN-SAT , - * ? / L C #
    if (CronExpressionValidator.isNotWildCard(expressionArray[4], /[\*\?]/gi)) {
        expressionArray[4] = CronExpressionValidator.convertDaysToInteger(expressionArray[4]);
        if (!CronExpressionValidator.segmentValidator("([0-9LC#\\\\,-\\/])", expressionArray[4], [1, 7], "days of the week")) {
            return false;
        }
    }

    // [5] Year empty or 1970-2099 , - * /
    if (len == 6) {
        if (CronExpressionValidator.isNotWildCard(expressionArray[5], /[\*]/gi)) {
            if (!CronExpressionValidator.segmentValidator("([0-9\\\\,-\\/])", expressionArray[6], [1970, 2099], "years")) {
                return false;
            }
        }
    }
    return true;
};

// ----------------------------------
// isNotWildcard 静态方法;
// ----------------------------------
CronExpressionValidator.isNotWildCard = function (value, expression) {
    let value_match = value.match(expression);
    return (value_match == null || value_match.length == 0) ? true : false;
};

// ----------------------------------
// convertDaysToInteger 静态方法;
// ----------------------------------
CronExpressionValidator.convertDaysToInteger = function (value) {
    let v = value;
    v = v.replace(/SUN/gi, "1");
    v = v.replace(/MON/gi, "2");
    v = v.replace(/TUE/gi, "3");
    v = v.replace(/WED/gi, "4");
    v = v.replace(/THU/gi, "5");
    v = v.replace(/FRI/gi, "6");
    v = v.replace(/SAT/gi, "7");
    return v;
};

// ----------------------------------
// convertMonthsToInteger 静态方法;
// ----------------------------------
CronExpressionValidator.convertMonthsToInteger = function (value) {
    let v = value;
    v = v.replace(/JAN/gi, "1");
    v = v.replace(/FEB/gi, "2");
    v = v.replace(/MAR/gi, "3");
    v = v.replace(/APR/gi, "4");
    v = v.replace(/MAY/gi, "5");
    v = v.replace(/JUN/gi, "6");
    v = v.replace(/JUL/gi, "7");
    v = v.replace(/AUG/gi, "8");
    v = v.replace(/SEP/gi, "9");
    v = v.replace(/OCT/gi, "10");
    v = v.replace(/NOV/gi, "11");
    v = v.replace(/DEC/gi, "12");
    return v;
};

// ----------------------------------
// segmentValidator 静态方法;
// ----------------------------------
CronExpressionValidator.segmentValidator = function (expression, value, range, segmentName) {
    let v = value;
    let numbers = new Array();

    // first, check for any improper segments
    let reg = new RegExp(expression, "gi");
    if (!reg.test(v)) {
        return false;
    }

    // check duplicate types
    // check only one L
    let dupMatch = value.match(/L/gi);
    if (dupMatch != null && dupMatch.length > 1) {
        return false;
    }

    // look through the segments
    // break up segments on ','
    // check for special cases L,W,C,/,#,-
    let split = v.split(",");
    let i = -1;
    let l = split.length;
    let match;

    while (++i < l) {
        // set vars
        let checkSegment = split[i];
        let n;
        let pattern = /(\w*)/;
        match = pattern.exec(checkSegment);

        // if just number
        pattern = /(\w*)\-?\d+(\w*)/;
        match = pattern.exec(checkSegment);

        if (match
            && match[0] == checkSegment
            && checkSegment.indexOf("L") == -1
            && checkSegment.indexOf("l") == -1
            && checkSegment.indexOf("C") == -1
            && checkSegment.indexOf("c") == -1
            && checkSegment.indexOf("W") == -1
            && checkSegment.indexOf("w") == -1
            && checkSegment.indexOf("/") == -1
            && (checkSegment.indexOf("-") == -1 || checkSegment
                .indexOf("-") == 0) && checkSegment.indexOf("#") == -1) {
            n = match[0];

            if (n && !(isNaN(n)))
                numbers.push(n);
            else if (match[0] == "0")
                numbers.push(n);
            continue;
        }
        // includes L, C, or w
        pattern = /(\w*)L|C|W(\w*)/i;
        match = pattern.exec(checkSegment);

        if (match
            && match[0] != ""
            && (checkSegment.indexOf("L") > -1
                || checkSegment.indexOf("l") > -1
                || checkSegment.indexOf("C") > -1
                || checkSegment.indexOf("c") > -1
                || checkSegment.indexOf("W") > -1 || checkSegment
                    .indexOf("w") > -1)) {

            // check just l or L
            if (checkSegment == "L" || checkSegment == "l")
                continue;
            pattern = /(\w*)\d+(l|c|w)?(\w*)/i;
            match = pattern.exec(checkSegment);

            // if something before or after
            if (!match || match[0] != checkSegment) {
                continue;
            }

            // get the number
            let numCheck = match[0];
            numCheck = numCheck.replace(/(l|c|w)/ig, "");

            n = Number(numCheck);

            if (n && !(isNaN(n)))
                numbers.push(n);
            else if (match[0] == "0")
                numbers.push(n);
            continue;
        }

        let numberSplit;

        // includes /
        if (checkSegment.indexOf("/") > -1) {
            // take first #
            numberSplit = checkSegment.split("/");

            if (numberSplit.length != 2) {
                continue;
            } else {
                n = numberSplit[0];

                if (n && !(isNaN(n)))
                    numbers.push(n);
                else if (numberSplit[0] == "0")
                    numbers.push(n);
                continue;
            }
        }

        // includes #
        if (checkSegment.indexOf("#") > -1) {
            // take first #
            numberSplit = checkSegment.split("#");

            if (numberSplit.length != 2) {
                continue;
            } else {
                n = numberSplit[0];

                if (n && !(isNaN(n)))
                    numbers.push(n);
                else if (numberSplit[0] == "0")
                    numbers.push(n);
                continue;
            }
        }

        // includes -
        if (checkSegment.indexOf("-") > 0) {
            // take both #
            numberSplit = checkSegment.split("-");

            if (numberSplit.length != 2) {
                continue;
            } else if (Number(numberSplit[0]) > Number(numberSplit[1])) {
                continue;
            } else {
                n = numberSplit[0];

                if (n && !(isNaN(n)))
                    numbers.push(n);
                else if (numberSplit[0] == "0")
                    numbers.push(n);
                n = numberSplit[1];

                if (n && !(isNaN(n)))
                    numbers.push(n);
                else if (numberSplit[1] == "0")
                    numbers.push(n);
                continue;
            }
        }

    }
    // lastly, check that all the found numbers are in range
    i = -1;
    l = numbers.length;

    if (l == 0)
        return false;

    while (++i < l) {
        // alert(numbers[i]);
        if (numbers[i] < range[0] || numbers[i] > range[1]) {
            return false;
        }
    }
    return true;
};