%# need a "branch" parameter

<form class="quick-search" action="/search" method="POST">
  <input type="hidden" name="branch" value="{{branch}}">
  <input type="text" value="" name="keyword" size="30"/>
  <select name="searchon" size="1">
    <option selected="selected" value="package"> package names</option>
    <option value="source">source package names</option>
    <option value="path">package contents</option>
  </select>
  <input type="submit" value="Search">
</form>
