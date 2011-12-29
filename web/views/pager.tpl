%# assume default limit is 50

%if start > 1:
  %if start - limit > 1:
    %if limit == 50:
      <a href="{{url}}?start={{start - limit}}">prev</a>
    %else:
      <a href="{{url}}?start={{start - limit}}&limit={{limit}}">prev</a>
    %end
  %else:
    %if limit == 50:
      <a href="{{url}}">prev</a>
    %else:
      <a href="{{url}}?limit={{limit}}">prev</a>
    %end
  %end
%end

%if start + limit - 1 < total:
  %if limit == 50:
    <a href="{{url}}?start={{start + limit}}">next</a>
  %else:
    <a href="{{url}}?start={{start + limit}}&limit={{limit}}">next</a>
  %end
%end

