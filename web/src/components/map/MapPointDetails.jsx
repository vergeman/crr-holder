export default function MapPointDetails({ detail, position, mwhNumber }) {
  return (
    <div className="map-point-details" style={position} aria-live="polite">
      <table aria-label="Settlement point holdings">
        <tbody>
          <tr>
            <th scope="row">SP name</th>
            <td>
              <strong>{detail.settlementPoint}</strong>
            </td>
          </tr>
          <tr>
            <th scope="row">Source MWh</th>
            <td>{mwhNumber.format(detail.sourceMwh)}</td>
          </tr>
          <tr>
            <th scope="row">Sink MWh</th>
            <td>{mwhNumber.format(detail.sinkMwh)}</td>
          </tr>
        </tbody>
      </table>
    </div>
  );
}
